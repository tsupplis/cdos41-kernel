"""Run selection and concrete command construction, without executing programs."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "runjob.h"
static struct fm_browser b;static struct fm_file f[3],saved[3];
static struct fm_marks m;static char *names[3],command[80],message[100];
static int calls,reports,launchok,reportok;
int invoke(s)char *s;{++calls;strcpy(command,s);return launchok;}
int report(s)char *s;{++reports;strcpy(message,s);return reportok;}
static struct fm_runner ops={invoke,report};
void reset(void)
{
 int i;memset(&b,0,sizeof(b));memset(f,0,sizeof(f));fm_marks_clear(&m);
 strcpy(f[0].name,"ZLAST.CMD   ");strcpy(f[1].name,"AFIRST.COM  ");strcpy(f[2].name,"MIDDLE.EXE  ");
 for(i=0;i<3;++i){names[i]=f[i].name;memset(f[i].raw,0x37,32);}
 fm_directory_sort(names,3);b.names=names;b.navigation.count=3;b.navigation.selected=2;
 calls=reports=0;launchok=reportok=1;command[0]=message[0]=0;
}
int run(void){int result;memcpy(saved,f,sizeof(f));result=fm_run_file(&b,f,3,&m,2,&ops);assert(!memcmp(saved,f,sizeof(f)));return result;}
int main(void)
{
 int i;char *types[]={"tool.cmd","tool.CoM","tool.ExE","tool.bAt"};
 char *invalid[]={"TOOL.TXT","NOEXT","A.C","A.CMD.X","A*.CMD","A?.CMD","A B.CMD","A;X.CMD","A:TOOL.CMD","../A.CMD","123456789.CMD"};
 reset();assert(run()==1 && calls==1 && !strcmp(command,"B:MIDDLE.EXE") && !m.count);
 reset();fm_marks_key(&m,3,3,44);assert(run()==1 && !strcmp(command,"B:ZLAST.CMD") && !m.count);
 for(i=0;i<4;++i){reset();strcpy(f[2].name,types[i]);assert(run()==1 && calls==1 && !m.count);}
 reset();strcpy(f[2].name,"12345678.CMD");assert(fm_run_file(&b,f,3,&m,16,&ops)==1);assert(!strcmp(command,"P:12345678.CMD") && strlen(command)==14);
 reset();fm_marks_key(&m,1,3,44);fm_marks_key(&m,3,3,44);assert(run()==0 && !calls && m.count==2 && !strcmp(message,"Please select one file"));
 for(i=0;i<11;++i){reset();strncpy(f[2].name,invalid[i],13);assert(run()==0 && !calls && m.count==1 && m.value[1]);}
 reset();strcpy(f[2].name,"TOOL.TXT");assert(run()==0 && !strcmp(message,"Bad file type, only .CMD, .COM, .EXE, or .BAT files "));
 reset();memset(f[2].name,'A',13);assert(run()==0 && !calls);
 reset();f[2].directory=1;assert(run()==0 && !calls && m.count==1);
 reset();launchok=0;assert(run()==0 && calls==1 && m.count==1 && m.value[1]);
 reset();reportok=0;strcpy(f[2].name,"TOOL.TXT");assert(run()==-1 && !calls && m.count==1);
 reset();b.navigation.count=b.navigation.selected=0;assert(run()==0 && !calls && !m.count);
 reset();assert(fm_run_file(&b,f,3,&m,0,&ops)==0 && !calls);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),*[str(root/(m+'.c')) for m in ('runjob','marks','dirlist')],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: Run sorted identities, single selection, fallback, executable types, concrete bounded commands and retained failures')
