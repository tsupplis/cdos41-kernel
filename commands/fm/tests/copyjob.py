"""Copy orchestration with real marks and sorted directory identities."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "copyjob.h"
static struct fm_browser b;
static struct fm_file f[3],before[3];
static struct fm_marks m;
static struct fm_copier ops;
static char *names[3],*expected[3];
static int answer,confirms,calls,results[3],drive;
int notice(char *name){++confirms;return answer;}
int transfer(d,raw,dst,dma,cancel)
int d,dst;char *raw,*dma;int (*cancel)();
{
 assert(dst==1 && d==drive && calls<3 && raw==expected[calls]);
 return results[calls++];
}
void reset(void)
{
 int i;char *rawnames[]={"Z       TXT","A       TXT","M       TXT"};
 memset(&b,0,sizeof(b));memset(f,0,sizeof(f));fm_marks_clear(&m);
 memset(expected,0,sizeof(expected));memset(results,0,sizeof(results));
 answer=1;confirms=calls=0;drive=2;
 for(i=0;i<3;++i) {
  memset(f[i].raw,0x24,32);memcpy(f[i].raw+1,rawnames[i],11);
  fm_directory_name(f[i].raw,f[i].name,13);names[i]=f[i].name;
 }
 fm_directory_sort(names,3);
 b.names=names;b.navigation.count=3;b.navigation.selected=2;
 ops.notice=notice;ops.transfer=transfer;ops.cancel=0;
}
void all(void){int i;for(i=1;i<=3;++i)fm_marks_key(&m,i,3,44);}
int run(void)
{
 int r;struct fm_browser old;char *saved[3];
 memcpy(before,f,sizeof(f));memcpy(&old,&b,sizeof(b));
 memcpy(saved,names,sizeof(names));
 r=fm_copy_files(&b,f,3,&m,drive,1,0,&ops);
 assert(!memcmp(before,f,sizeof(f)) && !memcmp(&old,&b,sizeof(b)));
 assert(!memcmp(saved,names,sizeof(names)));
 return r;
}
int main(void)
{
 struct fm_marks saved;
 reset();all();expected[0]=f[1].raw;expected[1]=f[2].raw;expected[2]=f[0].raw;
 results[0]=results[1]=results[2]=1;
 assert(run()==1 && calls==3 && !m.count);
 reset();all();expected[0]=f[1].raw;expected[1]=f[2].raw;
 results[0]=1;results[1]=-1;
 assert(run()==-1 && calls==2 && m.count==2 && !m.value[0]);
 reset();all();expected[0]=f[1].raw;
 assert(run()==0 && calls==1 && m.count==3);
 reset();expected[0]=f[2].raw;results[0]=1;
 assert(run()==1 && calls==1 && !m.count);
 reset();expected[0]=f[2].raw;results[0]=-1;
 assert(run()==-1 && m.count==1 && m.value[1]);
 reset();all();drive=1;memcpy(&saved,&m,sizeof(m));
 assert(run()==-1 && !calls && !memcmp(&saved,&m,sizeof(m)));
 reset();f[2].directory=1;
 assert(run()==-1 && !calls && m.value[1]);
 reset();answer=0;
 assert(run()==-1 && !calls && m.value[1]);
 reset();b.navigation.selected=0;
 assert(run()==1 && !calls && !m.count);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),
                 *[str(root/(m+'.c')) for m in ('copyjob','marks','dirlist')],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: Copy sorted batch, cursor fallback, stop on failure/cancel, retained selections and source preservation')
