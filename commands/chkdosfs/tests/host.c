/* Host adapter for the SAME fat.c/check.c used by the native CMD. */
#include <stdio.h>
#include <stdlib.h>
#include "chkdosfs.h"
static FILE *image;
static long failat=-1,readcount,readfail=-1;
static FILE *trace,*readtrace;
int verbose,repair,wrote,scan_erased,rebuild_contiguous,recover_directories,read_file_data;
static char *answers;
static int writecount,writefail=-1;
rdsect(sector,buf)
long sector;
char *buf;
{
    if(readtrace) {
        char record[4]; int i;
        for(i=0;i<4;i++) record[i]=(sector>>(i*8))&255;
        fwrite(record,1,4,readtrace); fflush(readtrace);
    }
    if(readcount++==readfail || (long)sector==failat || sector>=vol.sectors) {
        printf("TEST READ FAILED\n"); return 0;
    }
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
    if(trace) {
        char header[4]; int i;
        for(i=0;i<4;i++) header[i]=(sector>>(i*8))&255;
        fwrite(header,1,4,trace); fwrite(buf,1,512,trace); fflush(trace);
    }
    printf("TEST WRITE ATTEMPT %ld\n",sector);
    if(writecount++==writefail) { printf("TEST WRITE FAILED\n"); return 0; }
    return fseek(image,sector*512,SEEK_SET)==0 && fwrite(buf,1,512,image)==512 && fflush(image)==0;
}
static void test_summary()
{
    printf("TEST READ COUNT %ld\n",readcount);
    if(trace) fclose(trace);
    if(readtrace) fclose(readtrace);
}
int main(argc,argv)
int argc;
char **argv;
{
    char boot[512],dpb[29];
    unsigned total,spc,root,nfat,fatsiz,base,clusters,i;
    atexit(test_summary);
    repair=argc>3;
    if(argc>6) repair=atoi(argv[6]);
    if(argc<2 || !(image=fopen(argv[1],repair ? "r+b" : "rb"))) return 2;
    if(repair) answers=argv[3][0]=='1' ? "NY" : argv[3][0]=='0' ? "NN" : argv[3];
    if(argc>4) writefail=atoi(argv[4]);
    if(argc>5) scan_erased=atoi(argv[5]);
    if(argc>7) readfail=atol(argv[7]);
    if(argc>8) rebuild_contiguous=atoi(argv[8]);
    if(argc>9) recover_directories=atoi(argv[9]);
    if(argc>10) read_file_data=atoi(argv[10]);
    if(getenv("CHKDOSFS_READ_TRACE")) readtrace=fopen(getenv("CHKDOSFS_READ_TRACE"),"wb");
    if(getenv("CHKDOSFS_TRACE")) trace=fopen(getenv("CHKDOSFS_TRACE"),"wb");
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
