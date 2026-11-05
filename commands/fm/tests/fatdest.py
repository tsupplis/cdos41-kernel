"""FAT alias ownership, mapping failures and directory identity checks."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r'''
#include <assert.h>
#include <string.h>
#include "fatdest.h"
static int locations[17][4],calls,mapfail,locfail,afterfail,newcluster=42;
static char raw[32],before[32],saved[128],*dma;
static int expectedsource=3,expectedalias;
int FMLOC(drive,out)
int drive,*out;
{
 if(drive==locfail || (afterfail && calls>=afterfail && drive==expectedalias))return 0;
 memcpy(out,locations[drive],4*sizeof(int));return 1;
}
int BDOS(fn,arg)
int fn;char *arg;
{
 int i,alias,src;
 if(fn==26){dma=arg;return 0;}
 assert(fn==15);++calls;
 src=(arg[0]&127);alias=arg[12]+13;
 assert(src==expectedsource && alias==expectedalias);
 assert((arg[0]&128)!=0 && dma==saved);
 for(i=13;i<36;++i)assert(!arg[i]);
 if((raw[1]&127)=='.')assert(arg[1]=='.');
 else assert(!memcmp(arg+1,"CHILD      ",11));
 if(mapfail)return 0x0bff;
 locations[alias][0]=locations[src][0];
 locations[alias][1]=locations[src][1];
 locations[alias][2]=newcluster;locations[alias][3]=1;
 memset(arg,0,36); /* Kernel may alter its private FCB, never the input. */
 return 0;
}
static int attempt(want)
int want;
{
 int r,sourcebefore[4];
 memcpy(sourcebefore,locations[expectedsource],sizeof(sourcebefore));
 r=fm_fat_destination(expectedsource,raw,saved);
 assert(r==want && dma==saved && !memcmp(raw,before,32));
 assert(!memcmp(sourcebefore,locations[expectedsource],sizeof(sourcebefore)));
 if(want>0)assert(!fm_fat_destination_error()[0]);
 else assert(fm_fat_destination_error()[0]);
 return 0;
}
int main(void)
{
 int i,oldcalls;
 memset(raw,0,32);memcpy(raw+1,"child      ",11);raw[16]=64;
 memcpy(before,raw,32);dma=saved;
 locations[3][0]=3;locations[3][1]=9;locations[3][2]=10;locations[3][3]=1;
 for(i=14;i<=16;++i){locations[i][0]=2;locations[i][2]=i;locations[i][3]=1;}
 attempt(0);assert(calls==0 && strstr(fm_fat_destination_error(),"No free"));
 for(i=14;i<=16;++i)assert(locations[i][0]==2 && locations[i][2]==i);
 memset(locations[14],0,sizeof(locations[14]));expectedalias=14;
 locfail=14;attempt(0);assert(!calls);locfail=0;
 mapfail=1;attempt(0);assert(calls==1 && !locations[14][3]);mapfail=0;
 attempt(14);assert(calls==2 && locations[15][2]==15 && locations[16][2]==16);
 newcluster=43;attempt(14);assert(calls==3 && locations[14][2]==43);
 /* Changed owned identity is relinquished, never silently borrowed back. */
 locations[14][1]++;memset(locations[15],0,sizeof(locations[15]));expectedalias=15;
 attempt(15);assert(calls==4 && locations[14][2]==43);
 /* Never use the source alias as the destination slot. */
 expectedsource=15;expectedalias=16;memset(locations[16],0,sizeof(locations[16]));
 newcluster=99;attempt(16);assert(calls==5 && locations[15][2]==43);
 /* Same physical location is rejected even though logical drives differ. */
 expectedsource=3;expectedalias=15;newcluster=10;attempt(-1);
 assert(strstr(fm_fat_destination_error(),"source"));
 /* Dot and dot-dot are concrete directory entries, not wildcard names. */
 memcpy(raw+1,".          ",11);memcpy(before,raw,32);attempt(-1);
 memcpy(raw+1,"..         ",11);memcpy(before,raw,32);newcluster=0;attempt(15);
 oldcalls=calls;raw[16]=0;memcpy(before,raw,32);attempt(0);assert(calls==oldcalls);
 raw[16]=64;raw[1]='?';memcpy(before,raw,32);attempt(0);assert(calls==oldcalls);
 memcpy(raw+1,"CHILD      ",11);memcpy(before,raw,32);
 locations[3][0]=0;attempt(0);assert(calls==oldcalls);locations[3][0]=3;
 locfail=3;attempt(0);assert(calls==oldcalls);locfail=0;
 /* A successfully mapped but unverifiable alias is never considered owned. */
 afterfail=calls+1;attempt(0);afterfail=0;
 expectedalias=16;newcluster=44;attempt(16);
 assert(locations[15][2]==0);
 assert(!fm_fat_destination(3,raw,0));
 /* Start a new collection using free slots, without resetting module state. */
 for(i=14;i<=16;++i)memset(locations[i],0,sizeof(locations[i]));
 expectedsource=3;expectedalias=14;newcluster=10;
 assert(fm_fat_capture(3,raw,saved)==14);assert(fm_fat_pin(14));
 assert(fm_fat_valid(14) && fm_fat_same(3,14));
 expectedalias=15;newcluster=20;
 assert(fm_fat_capture(3,raw,saved)==15);assert(fm_fat_pin(15));
 assert(fm_fat_valid(15) && !fm_fat_same(3,15));
 /* Navigation operates on a clone; neither of the pinned marks is changed. */
 memcpy(raw+1,".          ",11);memcpy(before,raw,32);
 expectedsource=14;expectedalias=16;newcluster=10;
 assert(fm_fat_clone(14,saved)==16);
 assert(locations[14][2]==10 && locations[15][2]==20);
 locations[16][2]=99; /* independent public directory navigation */
 assert(!fm_fat_refresh_owned(14) && !fm_fat_refresh_owned(15));
 assert(!fm_fat_refresh_owned(13));
 assert(fm_fat_refresh_owned(16) && fm_fat_valid(16));
 /* Revisiting the bookmark reuses the intentionally moved working alias. */
 newcluster=10;assert(fm_fat_clone(14,saved)==16);
 assert(locations[16][2]==10 && locations[14][2]==10);
 locations[16][2]=99; /* no refresh: ordinary validation must reject it */
 assert(fm_fat_valid(14) && fm_fat_valid(15) && !fm_fat_valid(16));
 expectedsource=3;oldcalls=calls;
 assert(!fm_fat_capture(3,raw,saved));assert(calls==oldcalls);
 assert(strstr(fm_fat_destination_error(),"No free"));
 /* A failed replacement leaves the original pinned bookmark intact. */
 memset(locations[16],0,sizeof(locations[16]));expectedalias=16;mapfail=1;
 assert(!fm_fat_capture(3,raw,saved));mapfail=0;
 assert(fm_fat_valid(14) && fm_fat_valid(15));
 newcluster=30;assert(fm_fat_capture(3,raw,saved)==16);
 assert(fm_fat_pin(16));
 oldcalls=calls;assert(!fm_fat_capture(3,raw,saved));assert(calls==oldcalls);
 assert(fm_fat_unpin(14)); /* commit replacement only after capture/pin */
 expectedalias=14;newcluster=40;assert(fm_fat_capture(3,raw,saved)==14);
 assert(locations[15][2]==20 && locations[16][2]==30);
 /* Stale identity is not accepted or silently reclaimed as module-owned. */
 locations[15][1]++;assert(!fm_fat_valid(15) && !fm_fat_pin(15));
 assert(!fm_fat_clone(15,saved));assert(dma==saved);
 assert(fm_fat_unpin(15));assert(!fm_fat_unpin(13));
 assert(!fm_fat_refresh_owned(15)); /* stale ownership cannot be adopted */
 assert(!fm_fat_valid(13) && !fm_fat_same(3,15));
 assert(!memcmp(raw,before,32) && dma==saved);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'fatdest.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: FAT destination alias ownership, inherited mappings, failures, identity and DMA restoration')
