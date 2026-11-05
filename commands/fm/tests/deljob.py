"""Delete orchestration with real marks and sorted directory identities."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "deljob.h"
static struct fm_browser b;
static struct fm_file f[3],before[3];
static struct fm_marks m;
static struct fm_eraser ops;
static char *names[3],*expected[3];
static int answer,confirms,calls,results[3],drive;
int confirm(void){++confirms;return answer;}
int erase(d,raw)
int d;char *raw;
{
 assert(d==drive && calls<3 && raw==expected[calls]);
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
 ops.confirm=confirm;ops.erase=erase;
}
void all(void){int i;for(i=1;i<=3;++i)fm_marks_key(&m,i,3,44);}
int run(void)
{
 int r;struct fm_browser old;char *saved[3];
 memcpy(before,f,sizeof(f));memcpy(&old,&b,sizeof(b));
 memcpy(saved,names,sizeof(names));
 r=fm_delete_files(&b,f,3,&m,drive,&ops);
 assert(!memcmp(before,f,sizeof(f)) && !memcmp(&old,&b,sizeof(b)));
 assert(!memcmp(saved,names,sizeof(names)));
 return r;
}
int main(void)
{
 struct fm_marks saved;char missing[13];
 /* One prompt, sorted pointer identities, and per-file result retention. */
 reset();all();expected[0]=f[1].raw;expected[1]=f[2].raw;expected[2]=f[0].raw;
 results[0]=results[2]=1;
 assert(run()==1 && confirms==1 && calls==3);
 assert(m.count==1 && !m.value[0] && m.value[1] && !m.value[2]);
 /* Negative/empty responses map to cancel; no marks or files change. */
 reset();all();answer=0;memcpy(&saved,&m,sizeof(m));
 assert(run()==2 && confirms==1 && !calls && !memcmp(&saved,&m,sizeof(m)));
 reset();answer=0;memcpy(&saved,&m,sizeof(m));
 assert(run()==2 && confirms==1 && !calls && !memcmp(&saved,&m,sizeof(m)));
 /* UI failure is distinct from cancellation and equally nondestructive. */
 reset();all();answer=-1;memcpy(&saved,&m,sizeof(m));
 assert(run()==0 && confirms==1 && !calls && !memcmp(&saved,&m,sizeof(m)));
 /* No marks falls back to cursor; failures mark it, success leaves clear. */
 reset();expected[0]=f[2].raw;
 assert(run()==1 && confirms==1 && calls==1 && m.count==1 && m.value[1]);
 reset();expected[0]=f[2].raw;results[0]=1;drive=16;
 assert(run()==1 && confirms==1 && calls==1 && !m.count);
 /* Explicit marks override cursor and retain failures independently. */
 reset();fm_marks_key(&m,3,3,44);expected[0]=f[0].raw;results[0]=1;drive=1;
 assert(run()==1 && calls==1 && !m.count);
 reset();all();expected[0]=f[1].raw;expected[1]=f[2].raw;expected[2]=f[0].raw;
 assert(run()==1 && calls==3 && m.count==3);
 /* Directories never reach erase, even when marked or cursor-selected. */
 reset();all();f[2].directory=1;expected[0]=f[1].raw;expected[1]=f[0].raw;
 results[0]=results[1]=1;
 assert(run()==1 && calls==2 && m.count==1 && m.value[1]);
 reset();f[2].directory=1;
 assert(run()==1 && !calls && m.count==1 && m.value[1]);
 /* Equal text is insufficient: a missing backing pointer is retained. */
 reset();strcpy(missing,f[2].name);names[1]=missing;
 assert(run()==1 && !calls && m.count==1 && m.value[1]);
 /* No selection or empty lists do not even request confirmation. */
 reset();b.navigation.selected=0;
 assert(run()==2 && !confirms && !calls && !m.count);
 reset();b.navigation.count=b.navigation.selected=0;
 assert(run()==2 && !confirms && !calls && !m.count);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),
                 *[str(root/(m+'.c')) for m in ('deljob','marks','dirlist')],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: Delete confirmation, sorted identities, fallback, retained failures, directories and unchanged files')
