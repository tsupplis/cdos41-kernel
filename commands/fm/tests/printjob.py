"""Print batch cleanup, selection ownership and native BDOS routing."""
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
source = r"""
#include <assert.h>
#include <string.h>
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "printjob.h"
static struct fm_browser b;
static struct fm_marks m;
static struct fm_file f[3];
static char *names[3], dma[128];
static struct fm_printer p;
static int attached,detached,opened,closed,outputs,formfeeds,keys,notices;
static int attachok,detachok,openfail,readfail,closefail,putfail,keyfail,noticefail;
static int cancelat,active,reads,physical,order[3];
static int calls[16],args[16],nc,available;
int BDOS(int fn,int arg) {
 assert(nc<16);calls[nc]=fn;args[nc++]=arg;
 if(fn==161) return available ? 0 : 255;
 if(fn==6 && arg==254) return available;
 return 0;
}
int attach(void) {++attached;return attachok;}
int detach(void) {++detached;return detachok;}
int put(int ch) {
 ++outputs;if(ch==12)++formfeeds;
 return outputs!=putfail;
}
int key(void) {
 ++keys;if(keys==keyfail)return -1;
 return keys==cancelat;
}
int notice(char *name) {
 assert(name==names[0] || name==names[1] || name==names[2]);
 ++notices;return !noticefail;
}
int fm_type_open(int drive,char *raw,char *restore) {
 assert(drive==2 && restore==dma);
 active=raw[0];order[opened++]=active;reads=0;
 return active!=openfail;
}
int fm_type_read(char *buf) {
 if(active==readfail)return -1;
 if(physical || reads++)return 0;
 memset(buf,26,128);buf[0]='A'+active;return 1;
}
int fm_type_close(void) {++closed;return active!=closefail;}
void reset(void) {
 int i;
 memset(&b,0,sizeof b);memset(f,0,sizeof f);fm_marks_clear(&m);
 for(i=0;i<3;++i) {f[i].name[0]='A'+i;f[i].raw[0]=i;}
 /* Sorted display order intentionally differs from file storage order. */
 names[0]=f[2].name;names[1]=f[0].name;names[2]=f[1].name;
 b.names=names;b.navigation.count=3;b.navigation.selected=1;
 p.attach=attach;p.detach=detach;p.put=put;p.key=key;p.notice=notice;
 attached=detached=opened=closed=outputs=formfeeds=keys=notices=0;
 attachok=detachok=1;openfail=readfail=closefail=-1;
 putfail=keyfail=noticefail=cancelat=physical=0;
}
void all(void) {int i;for(i=1;i<=3;++i)fm_marks_key(&m,i,3,44);}
int run(void) {return fm_print_files(&b,f,3,&m,2,dma,&p);}
int main(void) {
 reset();all();assert(run()==1);
 assert(order[0]==2 && order[1]==0 && order[2]==1);
 assert(attached==1 && detached==1 && opened==3 && closed==3);
 assert(outputs==6 && formfeeds==3 && keys==3 && m.count==0);
 reset();b.navigation.selected=2;assert(run()==1);
 assert(opened==1 && order[0]==0 && m.count==0);
 reset();b.navigation.selected=0;assert(run()==1 && !attached);
 reset();all();attachok=0;assert(run()==0);
 assert(m.count==3 && !opened && detached==0);
 reset();attachok=0;assert(run()==0 && m.count==1 && m.value[0]);
 reset();all();openfail=2;assert(run()==-1);
 assert(opened==3 && closed==2 && formfeeds==2 && detached==1);
 assert(m.count==1 && m.value[0]);
 reset();all();physical=1;assert(run()==1);
 assert(outputs==3 && formfeeds==3 && keys==0 && closed==3 && !m.count);
 reset();all();cancelat=2;assert(run()==1);
 assert(opened==2 && closed==2 && formfeeds==2 && detached==1);
 assert(m.count==2 && !m.value[0] && m.value[1] && m.value[2]);
 reset();all();putfail=1;assert(run()==-1);
 assert(opened==1 && closed==1 && formfeeds==1 && keys==0 && m.count==3 && detached==1);
 reset();all();putfail=2;assert(run()==-1);
 assert(opened==1 && closed==1 && m.count==3 && detached==1);
 reset();all();readfail=2;assert(run()==-1);
 assert(opened==3 && closed==3 && formfeeds==3 && m.count==1 && m.value[0] && detached==1);
 reset();all();closefail=2;assert(run()==-1);
 assert(closed==3 && formfeeds==3 && m.count==1 && m.value[0] && detached==1);
 reset();all();keyfail=1;assert(run()==-1 && closed==1 && m.count==3 && detached==1);
 reset();all();noticefail=1;assert(run()==-1);
 assert(keys==0 && outputs==1 && closed==1 && m.count==3 && detached==1);
 reset();detachok=0;assert(run()==-1 && detached==1 && !m.count);
 /* Native callbacks route only to the process's current list device. */
 nc=0;available=1;fm_printer_native(&p,notice);
 assert(p.notice==notice && (*p.attach)());
 assert((*p.put)(321));assert((*p.key)()==1);assert((*p.detach)());
 assert(nc==5 && calls[0]==161 && args[0]==0);
 assert(calls[1]==5 && args[1]==65);
 assert(calls[2]==6 && args[2]==254 && calls[3]==6 && args[3]==253);
 assert(calls[4]==159 && args[4]==0);
 nc=0;available=0;assert(!(*p.attach)());assert(!(*p.key)());
 assert(nc==2 && calls[0]==161 && calls[1]==6 && args[1]==254);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'check.c'
    src.write_text(source)
    exe=Path(tmp)/'check'
    subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype',
                    '-I',str(root),str(src),
                    *[str(root/name) for name in
                      ('printjob.c','prtext.c','marks.c','printio.c')],
                    '-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: Print batch selections, EOF, cancellation, failures, cleanup and native BDOS routing')
