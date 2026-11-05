"""Rename orchestration with real directory formatting/sorting and marks."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "renjob.h"
static struct fm_browser b;
static struct fm_file f[3];
static struct fm_marks m;
static struct fm_renamer ops;
static char *names[3],dma[128],original[3][32];
static char *answers[16],*expected[16];
static int actions[16],results[16],ai,ci,ri,reportok;
static char reports[16][80];
int ask(name,target)
char *name,*target;
{
 assert(ai<16 && expected[ai]);
 assert(!strncmp(name,expected[ai],strlen(expected[ai])));
 if(answers[ai])strcpy(target,answers[ai]);
 return actions[ai++];
}
int change(drive,raw,target,d,out)
int drive;char *raw,*target,*d,*out;
{
 int r,i;
 assert(drive==2 && d==dma);assert(ci<16);
 r=results[ci++];
 if(r==1){memcpy(out,raw,32);for(i=1;i<12;++i)out[i]=' ';
  out[1]=target[0];out[9]='T';out[10]='X';out[11]='T';}
 return r;
}
int report(s)
char *s;
{assert(ri<16);strcpy(reports[ri++],s);return reportok;}
void reset(void)
{
 int i;char *rawnames[]={"Z       TXT","A       TXT","M       TXT"};
 memset(&b,0,sizeof(b));fm_marks_clear(&m);
 memset(answers,0,sizeof(answers));memset(expected,0,sizeof(expected));
 memset(actions,0,sizeof(actions));memset(results,0,sizeof(results));
 ai=ci=ri=0;reportok=1;
 for(i=0;i<3;++i){memset(f[i].raw,0x24,32);memcpy(f[i].raw+1,rawnames[i],11);
  memcpy(original[i],f[i].raw,32);fm_directory_name(f[i].raw,f[i].name,13);
  names[i]=f[i].name;}
 fm_directory_sort(names,3);
 b.names=names;b.navigation.count=3;b.navigation.selected=2;
 ops.ask=ask;ops.change=change;ops.report=report;
}
void step(i,old,text,action)
int i,action;char *old,*text;
{expected[i]=old;answers[i]=text;actions[i]=action;}
void all(void)
{int i;for(i=1;i<=3;++i)fm_marks_key(&m,i,3,44);}
int run(void){return fm_rename_files(&b,f,3,&m,2,dma,&ops);}
int main(void)
{
 /* Sorted display order differs from backing array; success touches identity. */
 reset();all();step(0,"A.TXT","B.TXT",1);step(1,"M.TXT","",0);
 step(2,"Z.TXT","Y.TXT",1);results[0]=results[1]=1;
 assert(run()==1 && ai==3 && ci==2 && ri==0);
 assert(m.count==1 && m.value[1] && !m.value[0] && !m.value[2]);
 assert(!strncmp(f[1].name,"B.TXT",5) && !strncmp(f[0].name,"Y.TXT",5));
 assert(!memcmp(f[2].raw,original[2],32));
 assert(f[0].raw[0]==original[0][0] && f[0].raw[31]==original[0][31]);
 /* No explicit mark selects only the cursor; cancellation retains it. */
 reset();step(0,"M.TXT",0,-1);assert(run()==1 && ai==1 && ci==0);
 assert(m.count==1 && m.value[1]);
 reset();step(0,"M.TXT","N.TXT",1);results[0]=1;
 assert(run()==1 && !m.count && !strncmp(f[2].name,"N.TXT",5));
 /* Drive rejection and invalid parse both retry the same selected file. */
 reset();step(0,"M.TXT","A:N.TXT",1);step(1,"M.TXT","BAD",1);
 step(2,"M.TXT","N.TXT",1);results[0]=0;results[1]=1;
 assert(run()==1 && ai==3 && ci==2 && ri==2 && !m.count);
 assert(!strcmp(reports[0],"You cannot specify a drive."));
 assert(!strcmp(reports[1],"Name is too long, or invalid"));
 /* Collision and other failure retain marks and move to the next file. */
 reset();all();step(0,"A.TXT","B.TXT",1);step(1,"M.TXT","N.TXT",1);
 step(2,"Z.TXT","",1);results[0]=-2;results[1]=-1;
 assert(run()==1 && ai==3 && ci==2 && ri==2 && m.count==3);
 assert(!strcmp(reports[0],"File already EXISTS, not renamed"));
 assert(!strcmp(reports[1],"File not renamed"));
 assert(!memcmp(f[0].raw,original[0],32));assert(!memcmp(f[1].raw,original[1],32));
 assert(!memcmp(f[2].raw,original[2],32));
 /* Esc after a success retains current and unprocessed items. */
 reset();all();step(0,"A.TXT","B.TXT",1);step(1,"M.TXT",0,-1);results[0]=1;
 assert(run()==1 && ai==2 && ci==1 && m.count==2 && !m.value[0]);
 assert(m.value[1] && m.value[2]);
 /* Display errors are fatal, retaining the outstanding set. */
 reset();all();step(0,"A.TXT",0,-2);assert(run()==0 && m.count==3 && !ci);
 reset();all();step(0,"A.TXT","BAD",1);reportok=0;
 assert(run()==0 && ai==1 && ci==1 && m.count==3);
 /* Empty list is harmless, and marks override a different cursor. */
 reset();b.navigation.count=b.navigation.selected=0;assert(run()==1 && !ai);
 reset();fm_marks_key(&m,3,3,44);step(0,"Z.TXT","Y.TXT",1);results[0]=1;
 assert(run()==1 && ai==1 && !m.count && !strncmp(f[0].name,"Y.TXT",5));
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),
                 *[str(root/(m+'.c')) for m in ('renjob','marks','dirlist')],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: Rename sorted identities, fallback, retries, collisions, skip/cancel, updates and retained marks')
