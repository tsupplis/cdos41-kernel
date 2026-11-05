"""Mock native parse/rename calls; prove failures never mutate names or disk."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "renio.h"
static int parse_result,rename_result,parses,renames,bad_parse;
static char old[32],before[32],out[32],dma[128];
int BDOS(fn,arg)
int fn;char *arg;
{
 int i,j;char **p,*s,*f;
 if(fn==152) {
  ++parses;p=(char **)arg;s=p[0];f=p[1];
  memset(f,0,36);memset(f+1,' ',11);j=1;
  for(i=0;s[i];++i) {if(s[i]=='.')j=9;else f[j++]=s[i];}
  if(bad_parse)f[1]='?';
  return parse_result;
 }
 assert(fn==23);++renames;
 assert(arg[0]==3 && arg[16]==3);
 for(i=1;i<12;++i)assert(arg[i]==(old[i]&127));
 assert(!memcmp(arg+17,"NEW     TXT",11));
 for(i=12;i<16;++i)assert(!arg[i]);
 for(i=28;i<36;++i)assert(!arg[i]);
 return rename_result;
}
int attempt(s,want)
char *s;int want;
{
 char text[80],copy[80];int result;
 strcpy(text,s);strcpy(copy,s);memset(out,0x55,32);
 result=fm_rename_file(3,old,text,dma,out);
 assert(result==want && !memcmp(old,before,32) && !strcmp(text,copy));
 if(result!=1) {int i;for(i=0;i<32;++i)assert(out[i]==0x55);}
 return result;
}
int main(void)
{
 int i,p;char *invalid[]={"","A:","A:NEW.TXT","A/B","A\\B","*.*",
 "N?.TXT","A B"," A","A;PW","A,B","A=B",".TXT","123456789.TXT",
 "A.ABCD","A..B","A.","NEW.TXT X",0};
 memset(old,0x26,32);memcpy(old+1,"OLD     TXT",11);
 old[1]|=128;old[9]|=128;memcpy(before,old,32);
 assert(attempt("new.txt",1)==1);assert(parses==1 && renames==1);
 for(i=0;i<32;++i)if(i<1 || i>11)assert(out[i]==old[i]);
 for(i=1;i<12;++i)assert((out[i]&128)==(old[i]&128));
 assert((out[1]&127)=='N' && (out[9]&127)=='T');
 rename_result=0x08ff;attempt("NEW.TXT",-2);
 rename_result=0x03ff;attempt("NEW.TXT",-1);
 rename_result=0xff;attempt("NEW.TXT",-1);
 p=renames;parse_result=0xffff;attempt("NEW.TXT",0);
 parse_result=0x1234;attempt("NEW.TXT",0);
 parse_result=0;bad_parse=1;attempt("NEW.TXT",0);bad_parse=0;
 for(i=0;invalid[i];++i)attempt(invalid[i],0);
 assert(renames==p);
 assert(!fm_rename_file(0,old,"NEW.TXT",dma,out));
 assert(!fm_rename_file(3,old,"NEW.TXT",0,out));
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'renio.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: rename FCB layout, attributes, full-word collision, parse failures and concrete-name constraints')
