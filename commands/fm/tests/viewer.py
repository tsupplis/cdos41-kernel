"""Read-only viewer orchestration and BDOS stream restoration."""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
viewer=r'''
#include <assert.h>
#include <string.h>
#include "event.h"
#include "scan.h"
#include "marks.h"
#include "viewer.h"
static struct fm_console con;
static int mode, opens, closes, reads, keys, ids[4], held, failures;
static int acquire(void) { assert(!held); held=1; return 1; }
static int release(void) { assert(held); held=0; return 1; }
static int cell(int r,int c,int ch,int attr) {
 assert(held && r>=0 && r<24 && c>=0 && c<80 && attr==7);
 if(mode==6 && r==3 && c==0 && ch=='X') {++failures;return 0;}
 return 1;
}
static int key(void) { assert(!held); ++keys; return mode==2 || mode==3 ? 27 : 13; }
int __BDOS(int fn, void *arg) { assert(!held && fn==142); return 0; }
int fm_type_open(int drive,char *raw,char *dma) {
 assert(!held && drive==1 && dma); ids[opens++]=raw[1]; reads=0;
 return !(mode==4 && opens==1);
}
int fm_type_read(char *record) {
 int i; assert(!held); ++reads;
 if(mode==5) return -1;
 if(reads>1) return 0;
 for(i=0;i<128;++i) record[i]=26;
 if(mode==2) for(i=0;i<20;++i) record[i]=13;
 else record[0]='X';
 return 1;
}
int fm_type_close(void) { assert(!held); ++closes; return mode!=7; }
int main(void) {
 struct fm_browser b; struct fm_file files[2];struct fm_marks m;
 struct fm_canvas canvas; char *names[2],dma[128];int result;
 memset(&b,0,sizeof(b));memset(files,0,sizeof(files));
 strcpy(files[0].name,"ONE.TXT     ");strcpy(files[1].name,"TWO.TXT     ");
 files[0].raw[1]='1';files[1].raw[1]='2';
 names[0]=files[1].name;names[1]=files[0].name;
 b.names=names;b.navigation.count=2;b.navigation.selected=1;
 canvas.rows=24;canvas.columns=80;canvas.cell=cell;
 con.acquire=acquire;con.release=release;con.read=key;con.put=0;
 for(mode=0;mode<=7;++mode) {
  opens=closes=reads=keys=held=failures=0;con.held=0;fm_marks_clear(&m);
  if(mode!=1) {fm_marks_key(&m,1,2,44);fm_marks_key(&m,2,2,44);}
  result=fm_view_files(&b,files,2,&m,1,dma,&canvas,&con,7);
  assert(!held);
  if(mode==0) {
   assert(result==1 && opens==2 && closes==2 && m.count==0 && keys==2);
   assert(ids[0]=='2' && ids[1]=='1');
  } else if(mode==1) assert(result==1 && opens==1 && closes==1 && m.count==0);
  else if(mode==2) assert(result==1 && opens==1 && closes==1 && m.count==2);
  else if(mode==3) assert(result==1 && opens==1 && closes==1 && m.count==1 && m.value[1]);
  else if(mode==4) assert(result==-1 && opens==2 && closes==1 && m.count==1 && m.value[0]);
  else if(mode==5) assert(result==-1 && opens==2 && closes==2 && m.count==2);
  else if(mode==6) assert(result==0 && failures && opens==1 && closes==1 && m.count==2);
  else if(mode==7) assert(result==-1 && opens==2 && closes==2 && m.count==2);
 }
 return 0;
}
'''
io=r'''
#include <assert.h>
#include <string.h>
#include "typeio.h"
static char *dma, *saved, *buffer;
static int openc,readc,closec,dmachanges,openresult,readresult,closeresult;
int __BDOS(int fn,void *arg) {
 char *fcb=(char *)arg;int i;
 switch(fn) {
 case 15:
  ++openc;assert(fcb[0]==2);
  for(i=1;i<12;++i) assert(fcb[i]=='A');
  for(i=12;i<36;++i) assert(fcb[i]==0);
  return openresult;
 case 20: ++readc;assert(dma==buffer);return readresult;
 case 16: ++closec;return closeresult;
 case 26: ++dmachanges;dma=(char *)arg;return 0;
 default: assert(0);return 0;
 }
}
int main(void) {
 char raw[32],original[32],d[128],r[128];int i;
 memset(raw,193,sizeof(raw));memcpy(original,raw,32);
 saved=d;buffer=r;dma=d;
 assert(fm_type_read(r)==-1 && fm_type_close()==1);
 assert(!fm_type_open(0,raw,d) && !fm_type_open(17,raw,d));
 assert(!fm_type_open(2,0,d) && !fm_type_open(2,raw,0));assert(!openc);
 openresult=255;assert(!fm_type_open(2,raw,d));
 assert(fm_type_read(r)==-1 && !readc && fm_type_close()==1 && !closec);
 openresult=0;assert(fm_type_open(2,raw,d));assert(!fm_type_open(2,raw,d));
 assert(!memcmp(raw,original,32));
 assert(fm_type_read(0)==-1 && !readc);
 for(i=0;i<4;++i) {
  readresult=i==3 ? 255 : i;
  assert(fm_type_read(r)==(i==0 ? 1 : i==1 ? 0 : -1));
  assert(dma==saved && dmachanges==2*(i+1));
 }
 closeresult=255;assert(!fm_type_close() && dma==saved);
 assert(fm_type_read(r)==-1 && fm_type_close()==1 && closec==1);
 assert(fm_type_open(2,raw,d));closeresult=0;
 assert(fm_type_close() && closec==2 && dma==saved);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp)
 for name,source,units in [('viewer',viewer,['viewer.c','type.c','marks.c','conio.c','keys.c']),
                            ('typeio',io,['typeio.c'])]:
  src=tmp/(name+'.c');src.write_text(source);exe=tmp/name
  subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-Wno-implicit-function-declaration',
                  '-I',str(root),str(src),*[str(root/u) for u in units],'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print('PASS: viewer selection, cancellation, failures, locks and read-only DMA restoration')
