/* Native DR C BDOS adapter. Search does not change drive or FAT mapping.
 * DMA restoration is explicit: BDOS has no portable get-DMA service.
 */
#include "scan.h"
int BDOS();
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
       (BDOS(12,0)&65535)!=0x1441) return 0;
    for(i=0;i<36;++i) fcb[i]=0;
    fcb[0]=drive|128;
    for(i=1;i<12;++i) fcb[i]=entry[i]&127;
    return (BDOS(15,fcb)&255)==0;
}

/* Original CODE28F7/2952: extended MAKE/DELETE directories. CODE2A96:
 * extended CLOSE returns to root. Never permit wildcard or dot deletion.
 * Caller has verified FAT media. All FCB storage is private to this call.
 */
int fm_native_directory(drive,name,operation)
int drive,operation;char *name;
{
    char work[36];int i,n,c,ext,result,loc[4];
    int FMLOC();
    if(drive<1 || drive>16 || operation<0 || operation>2 ||
       (BDOS(12,0)&65535)!=0x1441) return 0;
    for(i=0;i<36;++i)work[i]=0;
    for(i=1;i<12;++i)work[i]=' ';
    work[0]=drive|128;
    if(!operation) {
        if(!FMLOC(drive,loc) || loc[0]<1 || loc[0]>13)return 0;
        if(!loc[2])return 1;
        return (BDOS(16,work)&255)!=255;
    }
    if(!name || !name[0] || name[0]=='.')return 0;
    n=1;ext=0;
    for(i=0;name[i];++i) {
        if(i>=12)return 0;
        c=name[i]&255;
        if(c=='.') {if(ext || n==1 || !name[i+1])return 0;ext=1;n=9;continue;}
        if(c<33 || c>126 || c=='?' || c=='*' || c==':' || c=='/' ||
           c=='\\' || c==';' || c==',' || c=='=' || c=='<' || c=='>' ||
           c=='|' || c=='"' || c=='[' || c==']' || (!ext && n>8) || n>11)return 0;
        if(c>='a' && c<='z')c=c-'a'+'A';
        work[n++]=c;
    }
    result=BDOS(operation==1?22:19,work)&255;
    return operation==1 ? result==0 : result!=255;
}
