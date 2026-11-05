/* Native DR C BDOS adapter. Search does not change drive or FAT mapping.
 * DMA restoration is explicit: BDOS has no portable get-DMA service.
 */
#include "scan.h"
static int getuser() { return __BDOS(32,255) & 255; }
static int setuser(user)
int user;
{ return __BDOS(32,user); }
static int setdma(address)
char *address;
{ return __BDOS(26,address); }
static int first(fcb)
char *fcb;
{ return __BDOS(17,fcb) & 255; }
static int next(fcb)
char *fcb;
{ return __BDOS(18,fcb) & 255; }
static struct fm_search_ops operations;
int fm_native_scan(drive,user,fat,files,capacity,count,restore_dma)
int drive,user,fat,capacity,*count;
struct fm_file *files;
char *restore_dma;
{
    /* DR C 1.11 emits incorrect relocations for static function addresses
     * in this aggregate initializer. Assign code pointers at runtime.
     */
    operations.getuser = getuser;
    operations.setuser = setuser;
    operations.setdma = setdma;
    operations.first = first;
    operations.next = next;
    return fm_scan(&operations,drive,user,fat,files,capacity,count,restore_dma);
}

/* Public BDOS direct input: test readiness before reading, preserving NUL.
 * No echo, no discarded type-ahead and no assumptions about BIOS scan pairs.
 */
int fm_native_key()
{
    int key;
    if (!(__BDOS(6,254)&1)) return -1;
    key=__BDOS(6,253)&255;
    return key;
}

/* Extended FCB open changes this process's FAT directory mapping.
 * No ordinary file is opened and no directory entry is written.
 */
int fm_native_enter(drive,entry)
int drive;
char *entry;
{
    char fcb[36];
    int i;
    if(drive<1 || drive>16 || !entry || !(entry[16]&64) ||
       (__BDOS(12,0)&65535)!=0x1441) return 0;
    for(i=0;i<36;++i) fcb[i]=0;
    fcb[0]=drive|128;
    for(i=1;i<12;++i) fcb[i]=entry[i]&127;
    return (__BDOS(15,fcb)&255)==0;
}
