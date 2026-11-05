"""Named-copy orchestration and strict local target parser, with real marks."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "copynam.h"
static struct fm_browser b;
static struct fm_file f[3],before[3];
static struct fm_marks m;
static struct fm_named_copier ops;
static char *names[3],dma[128],*answers[64],*wantname[64],*wanttarget[3];
static char *wantraw[3];
static int actions[64],results[3],dest[3],ai,ci,reports,reportok,source;
int cancel(void){return 0;}
int ask(name,target)
char *name,*target;
{
 assert(ai<64 && wantname[ai]);assert(!strcmp(name,wantname[ai]));
 if(answers[ai]){assert(strlen(answers[ai])<=15);strcpy(target,answers[ai]);}
 return actions[ai++];
}
int transfer(sd,raw,dd,traw,d,stop)
int sd,dd;char *raw,*traw,*d;int (*stop)();
{
 int i;
 assert(ci<3 && sd==source && dd==dest[ci] && raw==wantraw[ci]);
 assert(d==dma && stop==cancel && fm_copy_name_drive()==dd);
 assert(!traw[0] && !memcmp(traw+1,wanttarget[ci],11));
 for(i=12;i<32;++i)assert(!traw[i]);
 return results[ci++];
}
int report(text)
char *text;
{
 assert(!strcmp(text,"Name is too long, or invalid") ||
        !strcmp(text,"Source and destination are the same file"));
 ++reports;return reportok;
}
void reset(void)
{
 int i;char *rn[]={"Z       TXT","A       TXT","M       TXT"};
 memset(&b,0,sizeof(b));memset(f,0,sizeof(f));fm_marks_clear(&m);
 memset(answers,0,sizeof(answers));memset(wantname,0,sizeof(wantname));
 memset(actions,0,sizeof(actions));memset(results,0,sizeof(results));
 ai=ci=reports=0;reportok=1;source=2;
 for(i=0;i<3;++i){memset(f[i].raw,0x24,32);memcpy(f[i].raw+1,rn[i],11);
  f[i].raw[9]|=128;fm_directory_name(f[i].raw,f[i].name,13);names[i]=f[i].name;}
 fm_directory_sort(names,3);b.names=names;
 b.navigation.count=3;b.navigation.selected=2;
 ops.ask=ask;ops.transfer=transfer;ops.cancel=cancel;ops.report=report;
}
void all(void){int i;for(i=1;i<=3;++i)fm_marks_key(&m,i,3,44);}
void step(i,index,text,action)
int i,index,action;char *text;
{wantname[i]=f[index].name;answers[i]=text;actions[i]=action;}
void expect(i,index,drive,text,result)
int i,index,drive,result;char *text;
{wantraw[i]=f[index].raw;dest[i]=drive;wanttarget[i]=text;results[i]=result;}
int run(void)
{
 struct fm_browser old;char *saved[3];int r;
 memcpy(before,f,sizeof(f));memcpy(&old,&b,sizeof(b));memcpy(saved,names,sizeof(names));
 r=fm_copy_names(&b,f,3,&m,source,dma,&ops);
 assert(!memcmp(before,f,sizeof(f)) && !memcmp(&old,&b,sizeof(b)));
 assert(!memcmp(saved,names,sizeof(names)));return r;
}
int main(void)
{
 int i;char missing[13];
 char *bad[]={"A:","Q:X","1:X","A:B:C","*.*","N?.TXT","A/B","A\\B",
 "A;PASS","A B"," A","A ",".TXT","A.","A..B","123456789.TXT",
 "A.ABCD","A,B","A=B","A<B","A>B","A|B","A\"B","A[B","A]B",
 "A\001","A\177","A\200","P:12345678.ABCD",0};
 reset();all();step(0,1,"a:one.bin",1);step(1,2,"two",1);step(2,0,"p:LAST.DAT",1);
 expect(0,1,1,"ONE     BIN",1);expect(1,2,2,"TWO        ",1);
 expect(2,0,16,"LAST    DAT",1);
 assert(run()==1 && ai==3 && ci==3 && !reports && !m.count && fm_copy_name_drive()==16);
 /* Invalid target retries without transfer, then longest valid target. */
 reset();for(i=0;bad[i];++i)step(i,2,bad[i],1);
 step(i,2,"p:12345678.xyz",1);expect(0,2,16,"12345678XYZ",1);
 assert(run()==1 && ci==1 && ai==i+1 && reports==i && !m.count);
 /* Same canonical name on same drive retries; other drive is valid. */
 reset();f[2].raw[1]=(char)('m'|128);
 step(0,2,"m.txt",1);step(1,2,"b:M.TXT",1);step(2,2,"c:m.txt",1);
 expect(0,2,3,"M       TXT",1);
 assert(run()==1 && reports==2 && ai==3 && ci==1 && !m.count);
 /* Skip and empty answer retain marks, but process following entries. */
 reset();all();step(0,1,0,0);step(1,2,"",1);step(2,0,"NEW",1);
 expect(0,0,2,"NEW        ",1);
 assert(run()==1 && ci==1 && m.count==2 && m.value[0] && m.value[1] && !m.value[2]);
 reset();step(0,2,0,0);assert(run()==1 && m.count==1 && m.value[1] && !ci);
 /* Cancellation and UI/transfer errors preserve current and unprocessed. */
 reset();all();step(0,1,"NEW",1);step(1,2,0,-1);expect(0,1,2,"NEW        ",1);
 assert(run()==0 && ci==1 && ai==2 && m.count==2 && !m.value[0]);
 reset();step(0,2,0,-2);assert(run()==-1 && !ci && m.count==1);
 reset();step(0,2,"?",1);reportok=0;assert(run()==-1 && reports==1 && !ci && m.count==1);
 reset();step(0,2,"M.TXT",1);reportok=0;assert(run()==-1 && reports==1 && !ci);
 for(i=-1;i<=0;++i){reset();all();step(0,1,"d:N",1);expect(0,1,4,"N          ",i);
  assert(run()==i && ci==1 && ai==1 && m.count==3 && fm_copy_name_drive()==4);}
 /* Explicit marks override cursor, directories/missing pointers never transfer. */
 reset();fm_marks_key(&m,3,3,44);step(0,0,"NEW",1);expect(0,0,2,"NEW        ",1);
 assert(run()==1 && ci==1 && !m.count);
 reset();f[2].directory=1;assert(run()==-1 && !ai && !ci && m.count==1);
 reset();strcpy(missing,f[2].name);names[1]=missing;assert(run()==-1 && !ai && !ci && m.count==1);
 reset();b.navigation.count=b.navigation.selected=0;assert(run()==1 && !ai && !ci && !m.count);
 reset();source=0;assert(run()==-1 && !ai && !ci && !m.count);
 reset();source=17;assert(run()==-1 && !ai && !ci && !m.count);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),
                 *[str(root/(m+'.c')) for m in ('copynam','marks','dirlist')],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: Named-copy parsing, drives, same-file protection, sorted identities and retained selections')
