"""TERM.DAT rendering/discovery/state restoration against shipped table bytes."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
fixture=(root/'../../base/term.dat')
if not fixture.exists():fixture=Path('/Users/thierry/Projects/CPM86/cdos41-kernel/base/term.dat')
source=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "term.c"
static unsigned char fixture[]={FIXTURE};
static int user=7,multi=3,mode=5,keyvalue,opens,readrec,which,closed;
static intptr_t dmaoff=0x80,dmasegment=0x2000;
static unsigned char output[512];static int used;
int BDOS(fn,arg)int fn;intptr_t arg;
{
 char *p=(char*)arg;
 if(fn==12)return 0x1441;
 if(fn==153)return 2;
 if(fn==32){if(arg!=255)user=arg;return user;}
 if(fn==44){multi=arg;return 0;}
 if(fn==51){dmasegment=arg;return 0;}
 if(fn==26){dmaoff=arg;return 0;}
 if(fn==109){mode=arg;return 0;}
 if(fn==15){assert(user==0 && p[0]==16);++opens;
  if(opens==1){assert(!memcmp(p+1,"TERM3   DAT",11));return which?255:0;}
  assert(!memcmp(p+1,"TERM    DAT",11));return 0;}
 if(fn==135)return which==2?0:65535;
 if(fn==137){struct fm_term_queue *q=(struct fm_term_queue*)p;assert(!memcmp(q->name,"termdat ",8));*q->buffer=0x2222;return 0;}
 if(fn==139){struct fm_term_queue *q=(struct fm_term_queue*)p;assert(*q->buffer==0x2222);return 0;}
 if(fn==35){p[33]=17;p[34]=p[35]=0;return 0;}
 if(fn==20){assert(user==0 && multi==1 && dmasegment==0x1000);memcpy((void*)dmaoff,fixture+128*readrec++,128);return 0;}
 if(fn==16){++closed;return 0;}
 if(fn==2){assert(used<512);output[used++]=arg;return 0;}
 assert(0);return 0;
}
int DATASEG(){return 0x1000;}
int FMTSTATE(out)int*out;{out[0]=dmaoff;out[1]=dmasegment;out[2]=mode;out[3]=multi;return 1;}
int XINIT(){XDATA=0x1000;return 1;}
int XCALL(f,b,c,d)int f,b,c,d;{assert(f==16);return d==255?0x100:0x200;}
int FARBYTE(s,o)int s,o;{if(s==0x2222){assert(o<sizeof(fixture));return fixture[o];}assert(o==0x101);return 4;}
int FARWORD(s,o)int s,o;{assert(o==0x216 || o==0x218);return 0;}
int FARPUT(){assert(0);return 0;}
int FMLOCK(){assert(0);return 0;}
int fm_native_key(){return keyvalue;}
int main(){struct fm_canvas c;struct fm_console con;int i,p;
 for(which=0;which<3;++which){opens=readrec=closed=used=0;
  assert(fm_term_open(&c,&con));assert(serial && opens==(which==1?2:1) && closed==(which==2?0:1));
  assert(user==7 && multi==3 && dmaoff==0x80 && dmasegment==0x2000 && mode==0x8e);
  assert(c.rows==24 && c.columns==80);assert(!c.cell(1,2,'A',7));
  assert(fm_console_begin(&con));assert(c.cell(1,2,'A',7));assert(fm_console_end(&con));
  assert(used==8 && !memcmp(output,"\033Y!\042\033s0A",8));
  used=0;assert(fm_term_cursor(0));assert(used==3 && !memcmp(output,"\033x5",3));
  keyvalue=1;assert(con.read()==187);keyvalue=22;assert(con.read()==192);
  keyvalue=0;assert(con.read()==0);keyvalue=-1;assert(con.read()==-1);
  used=0;assert(fm_console_begin(&con));assert(c.cell(23,79,'Z',7));assert(fm_console_end(&con));
  assert(used==9 && !memcmp(output,"\033Y7o\033wZ\033v",9));
  assert(fm_term_close(&con));assert(mode==5 && user==7 && multi==3);
 }
 /* Malformed positions/strings are rejected before any output. */
 termseg=0;termsize=sizeof(fixture);memcpy(termdata,fixture,sizeof(fixture));
 p=tw(2048);termdata[p]=1;assert(!tvalidate());
 memcpy(termdata,fixture,sizeof(fixture));termdata[1536]=-1;termdata[1537]=127;assert(!tvalidate());
 return 0;}
'''.replace('FIXTURE',','.join(map(str,fixture.read_bytes())))
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'check.c';p.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-Wno-pointer-to-int-cast','-I',str(root),str(p),str(root/'conio.c'),str(root/'keys.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: shipped TERM.DAT cursor/attributes/wrap, serial keys, per-console and fallback files, state restoration, malformed tables')
