"""Mock BDOS filesystem: transactional binary copying and failure cleanup."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#include "copyio.h"
struct file {int live,drive,user,records,ro,handles;char name[11],data[512];};
struct handle {char *fcb;int slot,pos;};
static struct file files[20];
static struct handle handles[4];
static char raw[32],before[32],saved[128],*dma;
static int failfn,failat,hits,renamefail,rollbackfail,renames;
static int cancels,cancelat,searchfail,creates,currentuser,callbackuser;
static int lookup(drive,name)
int drive;char *name;
{int i;for(i=0;i<20;++i)if(files[i].live && files[i].drive==drive && files[i].user==currentuser &&
 !memcmp(files[i].name,name,11))return i;return -1;}
static int add(drive,name,records,ro)
int drive,records,ro;char *name;
{int i,j;for(i=0;i<20;++i)if(!files[i].live)break;assert(i<20);
 files[i].live=1;files[i].drive=drive;files[i].user=currentuser;files[i].records=records;
 files[i].ro=ro;files[i].handles=0;memcpy(files[i].name,name,11);
 for(j=0;j<512;++j)files[i].data[j]=(char)(j*17+drive);
 return i;}
static int attach(fcb,slot)
char *fcb;int slot;
{int i;for(i=0;i<4;++i)if(!handles[i].fcb)break;assert(i<4);
 handles[i].fcb=fcb;handles[i].slot=slot;handles[i].pos=0;
 ++files[slot].handles;return 0;}
int BDOS(fn,arg)
int fn;char *arg;
{
 int i,j,r,slot,drive;
 if(fn==26){dma=arg;return 0;}
 if(fn==32){if((long)arg==255)return currentuser;currentuser=(int)(long)arg;return currentuser;}
 if(fn==17 && searchfail)return 0x03ff;
 if(fn==23){++renames;if(renames==renamefail || renames==rollbackfail)return 0x08ff;}
 if(fn==failfn && ++hits==failat)return fn==20 || fn==21 ? 2 : 0x03ff;
 drive=arg[0]&127;assert(drive==1 || drive==2);
 slot=lookup(drive,arg+1);
 if(fn==17){
  if(slot<0)return 255;memset(dma,0,128);
  memcpy(dma+65,arg+1,11);if(files[slot].ro)dma[73]|=128;
  return 2;
 }
 if(fn==15){if(slot<0)return 255;return attach(arg,slot);}
 if(fn==22){++creates;if(slot>=0)return 0x08ff;
  slot=add(drive,arg+1,0,0);return attach(arg,slot);}
 if(fn==19){if(slot<0 || files[slot].ro || files[slot].handles)return 255;
  assert(slot!=0);files[slot].live=0;return 0;}
 if(fn==23){
  assert(arg[16]==drive);
  if(slot<0 || files[slot].ro || files[slot].handles ||
    lookup(drive,arg+17)>=0)return 0x08ff;
  assert(slot!=0);memcpy(files[slot].name,arg+17,11);return 0;
 }
 for(i=0;i<4;++i)if(handles[i].fcb==arg)break;
 assert(i<4);slot=handles[i].slot;r=handles[i].pos;
 assert(files[slot].user==currentuser);
 if(fn==16){--files[slot].handles;handles[i].fcb=0;return 0;}
 if(fn==20){assert(slot==0);
  if(r==files[slot].records)return 1;
  memcpy(dma,files[slot].data+r*128,128);++handles[i].pos;return 0;}
 assert(fn==21 && slot!=0 && r<4);
 memcpy(files[slot].data+r*128,dma,128);
 ++handles[i].pos;files[slot].records=handles[i].pos;return 0;
}
static int cancel(){if(callbackuser>=0)currentuser=callbackuser;return ++cancels==cancelat;}
static int reset(existing)
int existing;
{
 int i;
 memset(files,0,sizeof(files));memset(handles,0,sizeof(handles));
 failfn=failat=hits=renamefail=rollbackfail=renames=0;
 cancels=cancelat=searchfail=creates=0;dma=saved;currentuser=3;callbackuser=-1;
 memset(raw,0,32);memcpy(raw+1,"SOURCE  BIN",11);
 raw[9]|=128;raw[10]|=128;raw[11]|=128;
 memcpy(before,raw,32);add(1,"SOURCE  BIN",3,1);
 /* Deliberate embedded text EOF followed by binary data. */
 files[0].data[2]=26;files[0].data[3]=0;files[0].data[4]=(char)255;
 if(existing)add(2,"SOURCE  BIN",1,0);
 return 0;
}
static int attempt(want)
int want;
{
 int i,r;char content[512];memcpy(content,files[0].data,512);
 r=fm_copy_file(1,raw,2,saved,cancel);
 assert(r==want && currentuser==3 && dma==saved && !memcmp(raw,before,32));
 assert(files[0].live && files[0].ro && !memcmp(content,files[0].data,512));
 for(i=0;i<4;++i)assert(!handles[i].fcb);
 return 0;
}
static int clean(original)
int original;
{
 int i,n=0;
 for(i=0;i<20;++i)if(files[i].live && files[i].drive==2)++n;
 assert(n==original);
 if(original){i=lookup(2,"SOURCE  BIN");assert(i>=0 && files[i].records==1);}
 assert(!fm_copy_recovery()[0]);return 0;
}
int main(void)
{
 int i,s,old;char orig[512],target[32],targetbefore[32];
 for(i=0;i<2;++i){reset(i);attempt(1);s=lookup(2,"SOURCE  BIN");
  assert(s>=0 && files[s].records==3 && !files[s].ro);
  assert(!memcmp(files[s].data,files[0].data,384));
  assert(!fm_copy_recovery()[0]);}
 reset(0);files[0].records=0;attempt(1);s=lookup(2,"SOURCE  BIN");
 assert(s>=0 && !files[s].records);
 /* Failure at every I/O stage preserves an existing target. */
 for(i=0;i<5;++i){int fns[]={15,22,20,21,16};reset(1);
  memcpy(orig,files[1].data,512);failfn=fns[i];failat=1;
  attempt(-1);clean(1);assert(!memcmp(orig,files[1].data,512));}
 reset(1);failfn=16;failat=2;attempt(-1);clean(1);
 reset(1);failfn=20;failat=2;attempt(-1);clean(1);
 reset(1);failfn=21;failat=2;attempt(-1);clean(1);
 for(i=1;i<=9;++i){reset(1);cancelat=i;attempt(0);clean(1);}
 reset(1);files[1].ro=1;attempt(-1);clean(1);assert(!creates);
 reset(1);renamefail=1;attempt(-1);clean(1);
 reset(1);renamefail=2;attempt(-1);clean(1);assert(renames==3);
 reset(1);memcpy(orig,files[1].data,512);renamefail=2;rollbackfail=3;
 attempt(-1);assert(lookup(2,"SOURCE  BIN")<0);
 s=lookup(2,"FMCB0000$$$");assert(s>=0 && !memcmp(orig,files[s].data,512));
 assert(!strcmp(fm_copy_recovery(),"FMCB0000.$$$"));
 assert(lookup(2,"FMCP0000$$$")<0);
 reset(0);renamefail=1;attempt(-1);clean(0);
 reset(1);add(2,"FMCP0000$$$",2,0);add(2,"FMCB0000$$$",2,0);
 memcpy(orig,files[2].data,512);attempt(1);
 assert(files[2].live && !memcmp(orig,files[2].data,512));
 assert(files[3].live && lookup(2,"FMCB0000$$$")==3);
 reset(0);searchfail=1;attempt(-1);clean(0);assert(!creates);
 reset(0);raw[1]='?';memcpy(before,raw,32);attempt(-1);clean(0);
 reset(0);assert(fm_copy_file(1,raw,1,saved,0)==-1 && dma==saved);
 assert(fm_copy_file(0,raw,2,saved,0)==-1 && dma==saved);
 assert(fm_copy_file(1,raw,2,0,0)==-1);
 reset(1);failfn=19;failat=1;attempt(-1);
 assert(!strcmp(fm_copy_recovery(),"FMCB0000.$$$"));
 s=lookup(2,"SOURCE  BIN");assert(s>=0 && files[s].records==3);
 assert(lookup(2,"FMCB0000$$$")>=0);
 fm_copy_reset();assert(!fm_copy_recovery()[0]);
 assert(lookup(2,"FMCB0000$$$")>=0);
 assert(lookup(2,"SOURCE  BIN")>=0 && dma==saved);
 /* Named copies keep the source FCB separate from all target operations. */
 for(i=1;i<=2;++i){reset(0);memset(target,0,32);
  memcpy(target+1,"renamed bin",11);target[9]|=128;
  memcpy(targetbefore,target,32);
  assert(fm_copy_named(1,raw,i,target,saved,cancel)==1);
  s=lookup(i,"RENAMED BIN");assert(s>=0 && files[s].records==3);
  assert(!memcmp(files[s].data,files[0].data,384));
  assert(!memcmp(target,targetbefore,32) && !memcmp(raw,before,32));
  assert(files[0].live && files[0].ro && dma==saved);
  assert(lookup(1,"SOURCE  BIN")==0);
 }
 reset(0);memset(target,0,32);memcpy(target+1,"source  bin",11);
 assert(fm_copy_named(1,raw,1,target,saved,cancel)==-1);
 assert(!creates && !renames && dma==saved);
 target[1]='?';assert(fm_copy_named(1,raw,2,target,saved,cancel)==-1);
 assert(!creates && !renames && dma==saved);
 assert(fm_copy_named(1,raw,2,0,saved,cancel)==-1);
 reset(0);memset(target,0,32);memcpy(target+1,"RENAMED BIN",11);
 old=add(1,"RENAMED BIN",1,0);memcpy(orig,files[old].data,512);
 renamefail=2;
 assert(fm_copy_named(1,raw,1,target,saved,cancel)==-1);
 assert(lookup(1,"RENAMED BIN")==old && !memcmp(orig,files[old].data,512));
 assert(lookup(1,"SOURCE  BIN")==0 && dma==saved);
 /* Target names resembling internal names must never alias our temp. */
 reset(0);memset(target,0,32);memcpy(target+1,"FMCP0000$$$",11);
 assert(fm_copy_named(1,raw,1,target,saved,cancel)==1);
 s=lookup(1,"FMCP0000$$$");assert(s>=0 && files[s].records==3);
 assert(lookup(1,"FMCP0001$$$")<0 && dma==saved);
 /* Cross-user copies switch before every disk operation, including closes.
  * The callback deliberately changes user to expose implicit-state errors. */
 reset(0);callbackuser=7;currentuser=9;
 assert(fm_copy_users(1,3,raw,1,5,raw,saved,cancel)==1);
 assert(currentuser==9 && dma==saved && !memcmp(raw,before,32));
 currentuser=5;s=lookup(1,"SOURCE  BIN");
 assert(s>=0 && files[s].records==3 && !memcmp(files[s].data,files[0].data,384));
 currentuser=3;assert(lookup(1,"SOURCE  BIN")==0 && files[0].ro);
 for(i=0;i<5;++i){int fns[]={15,22,20,21,16};reset(0);
  currentuser=5;old=add(2,"SOURCE  BIN",1,0);memcpy(orig,files[old].data,512);
  currentuser=9;callbackuser=7;failfn=fns[i];failat=1;
  assert(fm_copy_users(1,3,raw,2,5,raw,saved,cancel)==-1);
  assert(currentuser==9 && dma==saved);
  currentuser=5;assert(lookup(2,"SOURCE  BIN")==old);
  assert(!memcmp(orig,files[old].data,512));
  assert(lookup(2,"FMCP0000$$$")<0);
 }
 reset(0);currentuser=9;callbackuser=7;cancelat=3;
 assert(fm_copy_users(1,3,raw,2,5,raw,saved,cancel)==0);
 assert(currentuser==9 && dma==saved);
 currentuser=5;assert(lookup(2,"SOURCE  BIN")<0 && lookup(2,"FMCP0000$$$")<0);
 reset(0);currentuser=5;old=add(2,"SOURCE  BIN",1,0);
 memcpy(orig,files[old].data,512);currentuser=9;callbackuser=7;renamefail=2;
 assert(fm_copy_users(1,3,raw,2,5,raw,saved,cancel)==-1);
 assert(currentuser==9 && dma==saved);currentuser=5;
 assert(lookup(2,"SOURCE  BIN")==old && !memcmp(orig,files[old].data,512));
 reset(0);currentuser=9;
 assert(fm_copy_users(1,3,raw,1,3,raw,saved,cancel)==-1);
 assert(fm_copy_users(1,-1,raw,2,3,raw,saved,cancel)==-1);
 assert(fm_copy_users(1,3,raw,2,16,raw,saved,cancel)==-1);
 assert(currentuser==9 && dma==saved && !creates && !renames);
 for(i=0;i<4;++i)assert(!handles[i].fcb);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'copyio.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: binary copy, cancellation, I/O failures, collision protection, replacement and rollback recovery')
