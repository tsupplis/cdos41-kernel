"""Mock native erase: exact FCB, concrete names, and no input mutation."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "delio.h"
static int result,calls,drive;
static char raw[32];
int BDOS(fn,arg)
int fn;char *arg;
{
 int i;
 assert(fn==19);++calls;
 assert(arg[0]==drive);
 for(i=1;i<12;++i)assert(arg[i]==(raw[i]&127));
 for(i=12;i<36;++i)assert(arg[i]==0);
 /* Even a BDOS implementation that writes its FCB cannot change raw. */
 memset(arg,0x55,36);
 return result;
}
void attempt(want)
int want;
{
 char before[32];int n;
 memcpy(before,raw,32);n=calls;
 assert(fm_delete_file(drive,raw)==want);
 assert(!memcmp(raw,before,32));
 if(want)assert(calls==n+1);
}
int main(void)
{
 int i,j,n;char saved[32];
 char invalid[]="?*.:/\\;,=<>|\"[]\177\001";
 memset(raw,0x26,32);memcpy(raw+1,"OLD     TXT",11);
 for(i=1;i<12;++i)raw[i]|=128;
 memcpy(saved,raw,32);drive=3;
 result=0;attempt(1);
 result=3;attempt(1);
 result=0xff00;attempt(1);
 result=0xff;attempt(0);
 result=0x08ff;attempt(0);
 result=0xffff;attempt(0);
 assert(calls==6);result=0;
 drive=1;attempt(1);drive=16;attempt(1);
 n=calls;
 drive=0;attempt(0);drive=17;attempt(0);drive=-1;attempt(0);
 drive=3;
 assert(!fm_delete_file(drive,0));
 for(i=0;invalid[i];++i)for(j=1;j<12;++j) {
  memcpy(raw,saved,32);raw[j]=invalid[i];attempt(0);
  raw[j]|=128;attempt(0);
 }
 for(j=1;j<12;++j) {
  memcpy(raw,saved,32);raw[j]=0;attempt(0);
 }
 memcpy(raw,saved,32);memset(raw+1,' ',8);attempt(0);
 memset(raw+1,' ',11);attempt(0);
 assert(calls==n);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'delio.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: delete FCB, low-byte errors, attributes, unchanged inputs and rejected unsafe names')
