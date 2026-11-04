/* Host adapter for the SAME fat.c/check.c used by the native CMD. */
#include <stdio.h>
#include <stdlib.h>
#include "chkdosfs.h"
static FILE *image;
static long failat=-1;
int verbose,repair,wrote;
static char *answers;
static int writecount,writefail=-1;
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
confirm()
{ return *answers ? (*answers++=='Y') : 0; }
wrsect(sector,buf)
long sector;
char *buf;
{
    if(!repair || sector<0 || sector>=vol.sectors) return 0;
    wrote=1;
    if(writecount++==writefail) return 0;
    return fseek(image,sector*512,SEEK_SET)==0 && fwrite(buf,1,512,image)==512 && fflush(image)==0;
}
int main(argc,argv)
int argc;
char **argv;
{
    char boot[512],dpb[29];
    unsigned total,spc,root,nfat,fatsiz,base,clusters,i;
    repair=argc>3;
    if(argc<2 || !(image=fopen(argv[1],repair ? "r+b" : "rb"))) return 2;
    if(repair) answers=argv[3][0]=='1' ? "NY" : argv[3][0]=='0' ? "NN" : argv[3];
    if(argc>4) writefail=atoi(argv[4]);
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
    if(repair && !repairfs()) { fclose(image); return 2; }
    fclose(image); return errors ? 1 : 0;
}
