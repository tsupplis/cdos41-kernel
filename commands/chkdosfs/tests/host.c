/* Host adapter for the SAME fat.c/check.c used by the native CMD. */
#include <stdio.h>
#include <stdlib.h>
#include "chkdosfs.h"
static FILE *image;
static long failat=-1;
int verbose;
rdsect(sector,buf)
long sector;
char *buf;
{
    if((long)sector==failat || sector>=vol.sectors) return 0;
    return fseek(image,(long)sector*512,SEEK_SET)==0 &&
           fread(buf,1,512,image)==512;
}
static putword(p,n)
char *p;
unsigned n;
{ p[0]=n; p[1]=n>>8; return 0; }
int main(argc,argv)
int argc;
char **argv;
{
    char boot[512],dpb[29];
    unsigned total,spc,root,nfat,fatsiz,base,clusters,i;
    if(argc<2 || !(image=fopen(argv[1],"rb"))) return 2;
    if(argc>2) failat=atol(argv[2]);
    if(fread(boot,1,512,image)!=512) return 2;
    spc=boot[13]; root=wordget(boot+17); nfat=boot[16];
    fatsiz=wordget(boot+22); base=wordget(boot+14); total=wordget(boot+19);
    if(!spc || total<base+nfat*fatsiz+(root+15)/16) return 2;
    clusters=(total-base-nfat*fatsiz-(root+15)/16)/spc;
    for(i=0;i<29;i++) dpb[i]=0;
    putword(dpb,clusters<4085 ? 65535 : 65534);
    putword(dpb+2,nfat); putword(dpb+4,fatsiz); putword(dpb+6,clusters+2);
    putword(dpb+8,spc*512); putword(dpb+10,base);
    putword(dpb+19,root-1); dpb[27]=2;
    if(!geomset(dpb) || !fscheck()) { fclose(image); return 2; }
    fclose(image); return errors ? 1 : 0;
}
