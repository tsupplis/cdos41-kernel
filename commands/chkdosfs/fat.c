/* CHKDOSFS -- checked geometry and FAT access.
 * Corresponds to original DPB setup and get_fat_entry (CODE 156Eh).
 * Reads use a sector cache; repair updates every validated FAT copy.
 */
#include "chkdosfs.h"
struct volume vol;
int failed;
unsigned errors;
static char fatbuf[SECSIZE], nextbuf[SECSIZE];
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
    if(failed) return 0;
    /* Avoid the DRI 8086 long-division helper in the per-entry scan. */
    sec=vol.fatbase+(off>>9);
    if(off>=(long)vol.fatsiz*SECSIZE) { failed=1; return 0; }
    if(sec!=cached) {
        if(!rdsect(sec,fatbuf)) { failed=1; return 0; }
        cached=sec;
    }
    return fatbuf[(unsigned)off & (SECSIZE-1)]&255;
}

unsigned fatget(cluster)
unsigned cluster;
{
    unsigned a,b,v;
    long off;
    if(cluster>=vol.limit) { failed=1; return 0; }
    off=vol.fat16 ? ((long)cluster<<1) :
                   (((long)cluster*3)>>1);
    a=fatbyte(off); b=fatbyte(off+1);
    v=a|(b<<8);
    if(!vol.fat16) v=(cluster&1) ? v>>4 : v&4095;
    return v;
}

/* Commit a complete primary FAT sector to every copy. Same-sector entries
 * are updated together, avoiding a needless intermediate half-written entry.
 * FAT12 entries spanning sectors require two physical writes; both sectors
 * are read before either is changed. An I/O failure stops the sequence.
 */
static fatsector(sector,buf)
long sector;
char *buf;
{
    unsigned copy;
    if(!repair || failed || sector<vol.fatbase ||
       sector>=vol.fatbase+vol.fatsiz) return 0;
    for(copy=0;copy<vol.nfat;copy++) {
        if(!wrsect(sector+(long)copy*vol.fatsiz,buf)) {
            failed=1; cached=-1L; return 0;
        }
    }
    return 1;
}

fatset(cluster,value)
unsigned cluster,value;
{
    long off,sector;
    unsigned at,a,b;
    if(!repair || failed || cluster<2 || cluster>=vol.limit) return 0;
    if(!vol.fat16 && value>4095) return 0;
    off=vol.fat16 ? ((long)cluster<<1) : (((long)cluster*3)>>1);
    sector=vol.fatbase+(off>>9); at=(unsigned)off & (SECSIZE-1);
    if(off+1>=(long)vol.fatsiz*SECSIZE) return 0;
    fatbyte(off);
    if(failed) return 0;
    a=fatbuf[at]&255;
    if(at==SECSIZE-1) {
        if(!rdsect(sector+1,nextbuf)) { failed=1; return 0; }
        b=nextbuf[0]&255;
    } else b=fatbuf[at+1]&255;
    if(vol.fat16) { a=value&255; b=value>>8; }
    else if(cluster&1) { a=(a&15)|((value&15)<<4); b=value>>4; }
    else { a=value&255; b=(b&240)|((value>>8)&15); }
    fatbuf[at]=a;
    if(at==SECSIZE-1) nextbuf[0]=b;
    else fatbuf[at+1]=b;
    if(!fatsector(sector,fatbuf)) return 0;
    if(at==SECSIZE-1 && !fatsector(sector+1,nextbuf)) return 0;
    return 1;
}

/* A verification pass must reread the FAT from the physical disk. */
fatreset()
{ cached=-1L; return 0; }
