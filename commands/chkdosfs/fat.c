/* CHKDOSFS -- checked geometry and FAT access.
 * Corresponds to original DPB setup and get_fat_entry (CODE 156Eh).
 * No writes exist in this first, report-only implementation.
 */
#include "chkdosfs.h"
struct volume vol;
int failed;
unsigned errors;
static char fatbuf[SECSIZE];
static long cached;

unsigned wordget(p)
char *p;
{ return (unsigned)(p[0]&255) | ((unsigned)(p[1]&255)<<8); }

long longget(p)
char *p;
{
    if(wordget(p+2)&32768) return -1L;
    return (long)wordget(p) + (long)wordget(p+2)*65536L;
}

/* nclstrs includes the two reserved entries: valid clusters are [2,limit).
 * The kernel uses this exclusive bound too. Root size is DRM+1 entries.
 */
geomset(dpb)
char *dpb;
{
    unsigned flag, bytes;
    long need;
    failed=errors=0;
    cached=-1L;
    flag=wordget(dpb);
    if(flag!=65535 && flag!=65534) return 0;
    if(dpb[27]!=2) return 0;
    vol.fat16=flag==65534;
    vol.nfat=wordget(dpb+2); vol.fatsiz=wordget(dpb+4);
    vol.limit=wordget(dpb+6); bytes=wordget(dpb+8);
    vol.fatbase=wordget(dpb+10);
    if(wordget(dpb+19)==65535) return 0;
    vol.roots=wordget(dpb+19)+1;
    if(!vol.nfat || vol.nfat>4 || !vol.fatsiz || !vol.fatbase ||
       vol.limit<3 || !bytes || bytes%SECSIZE) return 0;
    vol.spc=bytes/SECSIZE;
    if(vol.spc & (vol.spc-1)) return 0;
    if((!vol.fat16 && vol.limit>4086) ||
       (vol.fat16 && vol.limit>65526)) return 0;
    need=vol.fat16 ? (long)vol.limit*2 :
                    ((long)vol.limit*3+1)/2;
    if(need>(long)vol.fatsiz*SECSIZE) return 0;
    vol.rootbase=vol.fatbase+(long)vol.nfat*vol.fatsiz;
    vol.database=vol.rootbase+((long)vol.roots*32+511)/512;
    vol.sectors=vol.database+(long)(vol.limit-2)*vol.spc;
    return vol.sectors>vol.database;
}

static fatbyte(off)
long off;
{
    long sec;
    sec=vol.fatbase+off/SECSIZE;
    if(off>=(long)vol.fatsiz*SECSIZE) { failed=1; return 0; }
    if(sec!=cached) {
        if(!rdsect(sec,fatbuf)) { failed=1; return 0; }
        cached=sec;
    }
    return fatbuf[(unsigned)(off%SECSIZE)]&255;
}

unsigned fatget(cluster)
unsigned cluster;
{
    unsigned a,b,v;
    long off;
    if(cluster>=vol.limit) { failed=1; return 0; }
    off=vol.fat16 ? (long)cluster*2 :
                   (long)cluster*3/2;
    a=fatbyte(off); b=fatbyte(off+1);
    v=a|(b<<8);
    if(!vol.fat16) v=(cluster&1) ? v>>4 : v&4095;
    return v;
}
