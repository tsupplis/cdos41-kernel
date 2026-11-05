"""Single-drive engine media swaps, transactional replacement, and cleanup."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#include "copyio.h"
struct file {int used,medium,ro,n;char name[11],data[40*128];};
static struct file f[8];static char raw[32],saved[128],*dma,*handle;
static int medium,user,drive,active,swaps,resets,failread,failwrite,failmake,failclose,failrename,failrestore,cancelat;
static int find(name)
char *name;{int i;for(i=0;i<8;++i)if(f[i].used && f[i].medium==medium && !memcmp(f[i].name,name,11))return i;return -1;}
int BDOS(fn,arg)
int fn;char *arg;
{
 int i,n,p;long v=(long)arg;
 if(fn==32){if(v==255)return user;user=v;return 0;}
 if(fn==25)return drive;
 if(fn==14){drive=v;return 0;}
 if(fn==26){dma=arg;return 0;}
 if(fn==13){assert(active<0);++resets;return 0;}
 assert(user==7);
 if(fn==17){i=find(arg+1);if(i<0)return 255;memset(dma,0,128);memcpy(dma+1,f[i].name,11);if(f[i].ro)dma[9]|=128;return 0;}
 if(fn==15 || fn==22){assert(active<0);i=find(arg+1);
  if(fn==22){if(failmake)return 255;assert(i<0);for(i=0;i<8 && f[i].used;++i);assert(i<8);f[i].used=1;f[i].medium=medium;memcpy(f[i].name,arg+1,11);f[i].n=0;}
  if(i<0)return 255;active=i;handle=arg;return 0;}
 if(fn==16){assert(active>=0 && arg==handle);if(failclose){failclose=0;return 255;}active=-1;return 0;}
 if(fn==33 || fn==34){assert(active>=0 && arg==handle);i=active;
  p=(arg[33]&255)+((arg[34]&255)<<8);assert(p<40);
  if(fn==33){if(failread && p==33)return 2;if(p>=f[i].n)return 4;memcpy(dma,f[i].data+p*128,128);return 0;}
  if(failwrite && p==33)return 2;memcpy(f[i].data+p*128,dma,128);if(p>=f[i].n)f[i].n=p+1;return 0;}
 if(fn==23){assert(active<0 && medium==1);if(failrename && arg[1]=='F'){failrename=0;return 255;}
  i=find(arg+1);n=find(arg+17);if(i<0 || n>=0)return 255;memcpy(f[i].name,arg+17,11);return 0;}
 assert(fn==19 && active<0 && medium==1);i=find(arg+1);if(i<0)return 255;f[i].used=0;return 0;
}
int ask(side)int side;
{assert(active<0 && dma==saved);++swaps;if(swaps==cancelat)return 0;if(failrestore && side==0)return 0;medium=side;return 1;}
int cancel(){return 0;}
static int reset()
{int i;memset(f,0,sizeof(f));memset(raw,0,sizeof(raw));memcpy(raw+1,"HELLO   BIN",11);
 medium=0;user=7;drive=1;active=-1;dma=saved;
 swaps=resets=failread=failwrite=failmake=failclose=failrename=failrestore=cancelat=0;
 f[0].used=1;f[0].medium=0;f[0].n=35;memcpy(f[0].name,raw+1,11);
 for(i=0;i<35*128;++i)f[0].data[i]=(i*17+26)&255;
 f[1].used=1;f[1].medium=1;f[1].n=1;memcpy(f[1].name,raw+1,11);memset(f[1].data,99,128);return 0;}
static int run()
{char before[35*128];int r;memcpy(before,f[0].data,sizeof(before));r=fm_copy_swapped(2,raw,7,saved,cancel,ask);
 assert(active<0 && dma==saved && user==7 && drive==1);assert(f[0].used && !memcmp(before,f[0].data,sizeof(before)));return r;}
static int old()
{int i,m; m=medium;medium=1;i=find(raw+1);medium=m;return i>=0 && f[i].n==1 && f[i].data[0]==99;}
int main(void)
{int i;
 reset();assert(run()==1 && swaps==4 && medium==0 && fm_copy_swap_ready());
 medium=1;i=find(raw+1);assert(i>=0 && f[i].n==35 && !memcmp(f[i].data,f[0].data,35*128));
 reset();f[1].ro=1;assert(run()==-1 && old());
 reset();failwrite=1;assert(run()==-1 && old());
 reset();failread=1;assert(run()==-1 && old() && *fm_copy_recovery());
 reset();failmake=1;assert(run()==-1 && old());
 reset();failclose=1;assert(run()==-1 && old());
 reset();failrename=1;assert(run()==-1 && old());
 reset();cancelat=2;assert(run()==0 && old() && *fm_copy_recovery());
 reset();failrestore=1;assert(run()==-1 && old() && !fm_copy_swap_ready());
 return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'copyio.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: single-drive chunks, binary records, rollback, cancellation and source restoration')
