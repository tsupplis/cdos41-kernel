"""Scratch-root path discovery preserves source, inherited aliases and pins."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "fatdest.c"
static int locations[17][4],user=7,fail,searches;
static char saved[128],*dma=saved;
int FMLOC(drive,out)
int drive,*out;
{memcpy(out,locations[drive],4*sizeof(int));return 1;}
int BDOS(fn,arg)
int fn;char *arg;
{
 int a,s,child;
 if(fn==32){if((intptr_t)arg!=255)user=(int)(intptr_t)arg;return user;}
 if(fn==26){dma=arg;return 0;}
 s=arg[0]&127;
 if(fn==15){
  assert(arg[0]&128);
  if(arg[12]){
   a=arg[12]+13;assert(a==16);
   memcpy(locations[a],locations[s],sizeof(locations[a]));locations[a][3]=1;
  } else {
   assert(s==16 && user==0 && arg[1]=='.' && arg[2]=='.');
   if(fail==1)return 0xff;
   locations[s][2]=locations[s][2]==20?10:0;
   if(fail==4)locations[s][2]=20;
   if(fail==5)locations[s][1]++;
  }
  return 0;
 }
 assert((fn==17 || fn==18) && s==16 && user==0);++searches;
 if(fail==2)return 0xff;
 if(fn==18)return 0xff;
 memset(dma,0,128);child=locations[s][2]?20:10;
 memcpy(dma+1,child==20?"DEEP    EXT":"SUB        ",11);
 dma[16]=64;dma[26]=child;
 if(fail==3)dma[1]='?';
 return 0;
}
static void setup(void){
 memset(locations,0,sizeof(locations));memset(owned,0,sizeof(owned));memset(pinned,0,sizeof(pinned));
 locations[3][0]=3;locations[3][1]=9;locations[3][2]=20;locations[3][3]=1;
 locations[14][0]=4;locations[14][1]=8;locations[14][2]=123;locations[14][3]=1;
 locations[15][0]=3;locations[15][1]=9;locations[15][2]=456;locations[15][3]=1;
 owned[1]=pinned[1]=1;memcpy(signature[1],locations[15],3*sizeof(int));
 user=7;dma=saved;searches=0;
}
int main(void){
 char path[80];int r,k,before[3][4];
 for(fail=0;fail<=5;++fail){
  setup();memcpy(before,locations+13,sizeof(before));
  r=fm_fat_root(3,path,sizeof(path),saved);
  assert(r==(fail?0:16));
  assert(user==7 && dma==saved && locations[3][2]==20);
  assert(!memcmp(before,locations+13,sizeof(before)) && pinned[1]);
  if(!fail){assert(!strcmp(path,"C:\\SUB\\DEEP.EXT"));assert(locations[16][2]==0 && fm_fat_valid(16));}
  else assert(!path[0] && fm_fat_destination_error()[0]);
 }
 fail=0;setup();assert(!fm_fat_root_protected(3,path,80,saved,16));assert(!searches && locations[3][2]==20);
 assert(fm_fat_root(3,path,80,saved)==16);
 setup();assert(!fm_fat_root(3,path,5,saved));assert(user==7 && dma==saved);
 setup();locations[3][2]=0;assert(fm_fat_root(3,path,4,saved)==16);assert(!strcmp(path,"C:\\") && !searches);
 setup();locations[16][0]=2;locations[16][3]=1;assert(!fm_fat_root(3,path,80,saved));assert(!searches);
 assert(!fm_fat_root(0,path,80,saved));assert(!fm_fat_root(3,0,80,saved));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'check.c';p.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-Wno-deprecated-non-prototype','-I',str(root),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: FAT full path/root, source and pin preservation, errors, cycles, media changes, bounds, caller state')
