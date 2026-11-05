"""Original external-tool descriptors, selected-name construction and failure retention."""
from pathlib import Path
import json,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
# Verify the actual CMD descriptor fields, not menu.command display aliases.
ref=root.parents[1]/'extra/fm.cmd'
if ref.exists() and (root/'menus.json').exists():
 data=ref.read_bytes();base=0xe3c0
 expected={
 'edit':('DREDIX.CMD',None), 'backup':('BACK.CMD',None),
 'disk_copy':('DSKMAINT.CMD','/COPY'),'disk_format':('DSKMAINT.CMD','/FORMAT'),
 'free_memory':('STOP.CMD',None),'load_function_keys':('FUNCTION.CMD',None),
 'assign_function_keys':('FUNCTION.CMD','!SETUP /PARAM'),
 'serial_ports':('SETPORT.CMD','!SETUP /PARAM'),'system_defaults':('SETUP.CMD',None),
 'memory_disk':('SETUP.CMD','/MDISK'),'boot_hard_disk':('HDMAINT.CMD','[F5,F6,F0,F0]'),
 'hard_disk_maintenance':('HDMAINT.CMD',None),'diskette_maintenance':('DSKMAINT.CMD',None)}
 def field(record,off):
  ptr=int.from_bytes(data[base+record+off:base+record+off+2],'little')
  return data[base+ptr:].split(b'\0',1)[0].decode('ascii') if ptr else None
 for item in json.loads((root/'menus.json').read_text()):
  if item['action'] in expected:
   assert (field(item['record'],16),field(item['record'],18))==expected[item['action']]
   assert all(field(item['record'],off) is None for off in (20,22,24,26))
  elif item['action']=='help': assert field(item['record'],8)=='HELP'
source=r'''
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "runjob.h"
#include "extjob.h"
static struct fm_browser b;static struct fm_file f[16],saved[16];
static struct fm_marks m;static char *names[16],command[128],message[100];
static int calls,reports,launchok,reportok,failcall,asks,answercount;
static char history[2][128];static char *answers[4];static int askresult;
int ask(s)char *s;{++asks;if(askresult!=1)return askresult;
 assert(asks<=answercount);strcpy(s,answers[asks-1]);return 1;}
int invoke(s)char *s;{++calls;assert(calls<=2);strcpy(history[calls-1],s);strcpy(command,s);return launchok && calls!=failcall;}
int report(s)char *s;{++reports;strcpy(message,s);return reportok;}
static struct fm_runner ops={invoke,report};
static int reset()
{
 int i;memset(&b,0,sizeof(b));memset(f,0,sizeof(f));fm_marks_clear(&m);
 strcpy(f[0].name,"ZLAST.TXT   ");strcpy(f[1].name,"AFIRST.TXT  ");strcpy(f[2].name,"MIDDLE.KEY  ");
 for(i=0;i<3;++i){names[i]=f[i].name;memset(f[i].raw,0x37,32);}
 fm_directory_sort(names,3);b.names=names;b.navigation.count=3;b.navigation.selected=2;
 calls=reports=failcall=asks=0;launchok=reportok=askresult=1;answercount=1;answers[0]="DOS";command[0]=message[0]=0;return 0;
}
static int run(index)
int index;
{int r;memcpy(saved,f,sizeof(f));r=fm_external(index,&b,f,16,&m,&ops);assert(!memcmp(saved,f,sizeof(f)));return r;}
static int boot()
{return fm_external_boot(&b,f,16,&m,ask,&ops);}
int main(void)
{
 int i;int ids[]={0,10,12,13,14,23,24,26,27};
 char *cmds[]={"HELP.CMD HELP","DREDIX.CMD","DSKMAINT.CMD /COPY",
 "DSKMAINT.CMD /FORMAT","STOP.CMD","SETUP.CMD","SETUP.CMD /MDISK",
 "HDMAINT.CMD","DSKMAINT.CMD"};
 for(i=0;i<9;++i){reset();assert(fm_external_available(ids[i]));
  assert(run(ids[i])==1 && calls==1 && !strcmp(command,cmds[i]) && !m.count);}
 reset();fm_marks_key(&m,3,3,44);assert(run(10)==1 && !strcmp(command,"DREDIX.CMD ZLAST.TXT") && !m.count);
 reset();fm_marks_key(&m,1,3,44);fm_marks_key(&m,3,3,44);
 assert(run(10)==0 && !calls && m.count==2 && !strcmp(message,"Too many files selected"));
 reset();launchok=0;fm_marks_key(&m,1,3,44);assert(run(10)==0 && calls==1 && m.count==1);
 reset();assert(run(20)==1 && !strcmp(command,"FUNCTION.CMD MIDDLE.KEY") && !m.count);
 reset();launchok=0;assert(run(20)==0 && m.count==1 && m.value[1]);
 reset();b.navigation.count=b.navigation.selected=0;b.names=0;
 assert(run(10)==1 && !strcmp(command,"DREDIX.CMD"));
 reset();b.navigation.count=b.navigation.selected=0;b.names=0;
 assert(run(20)==0 && !calls && !m.count);
 /* The original records specify NULL separators; do not invent spaces. */
 reset();fm_marks_key(&m,1,3,44);fm_marks_key(&m,3,3,44);
 assert(run(12)==1 && !strcmp(command,"DSKMAINT.CMD /COPYAFIRST.TXTZLAST.TXT"));
 reset();fm_marks_key(&m,1,3,44);fm_marks_key(&m,3,3,44);
 assert(run(0)==1 && !strcmp(command,"HELP.CMD HELP") && m.count==2);
 for(i=21;i<=22;++i){reset();fm_marks_key(&m,1,3,44);
  assert(fm_external_available(i) && run(i)==1 && calls==2 && !m.count);
  assert(!strcmp(history[0],i==21?"FUNCTION.CMD":"SETPORT.CMD"));
  assert(!strcmp(history[1],"SETUP.CMD /PARAMAFIRST.TXT"));}
 reset();assert(run(21)==1 && !strcmp(history[1],"SETUP.CMD /PARAM"));
 for(i=1;i<=2;++i){reset();failcall=i;fm_marks_key(&m,1,3,44);
  assert(run(21)==0 && calls==2 && m.count==1);}
 reset();fm_marks_key(&m,1,3,44);assert(boot()==1 && calls==1 && !m.count);
 assert(!strcmp(command,"HDMAINT.CMD [F5,F6,F0,F0]AFIRST.TXT"));
 reset();answers[0]="cp/m";assert(boot()==1 && !strcmp(command,"HDMAINT.CMD [F5,F4,F0,F0]"));
 reset();answercount=3;answers[0]="CPM";answers[1]="DOS ";answers[2]="dos";
 assert(boot()==1 && asks==3 && calls==1);
 reset();answers[0]="";fm_marks_key(&m,1,3,44);assert(boot()==0 && !calls && m.count==1);
 reset();askresult=0;fm_marks_key(&m,1,3,44);assert(boot()==0 && !calls && m.count==1);
 reset();askresult=-1;assert(boot()==-1 && !calls);
 reset();launchok=0;fm_marks_key(&m,1,3,44);assert(boot()==0 && calls==1 && m.count==1);
 reset();assert(!fm_external_available(9) && run(9)==0 && !calls);
 assert(!fm_external_available(25) && run(25)==0 && !calls);
 assert(!fm_external_available(6) && run(6)==0 && !calls);
 reset();f[2].directory=1;assert(run(20)==0 && !calls && m.count==1);
 reset();strcpy(f[2].name,"A!.TXT");assert(run(20)==0 && !calls && m.count==1);
 reset();names[1]="MISSING.TXT";assert(run(20)==0 && !calls && m.count==1);
 reset();reportok=0;assert(run(9)==-1 && !calls);
 reset();b.navigation.count=12;
 for(i=0;i<12;++i){strcpy(f[i].name,"LONGNAME.TXT");names[i]=f[i].name;fm_marks_key(&m,i+1,12,44);}
 assert(run(14)==0 && !calls && m.count==12 && !strcmp(message,"Too many files selected"));
 assert(run(21)==0 && !calls && m.count==12);
 assert(boot()==0 && !calls && m.count==12);
 reset();b.navigation.count=257;assert(run(10)==0 && !calls);
 assert(fm_external(10,&b,f,16,&m,0)==-1);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),*[str(root/(m+'.c')) for m in ('extjob','marks','dirlist')],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: external descriptors, bare selected names, optional Edit, bounds, known chains, boot prompts, bounds and retained failures')
