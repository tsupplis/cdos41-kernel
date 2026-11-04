/* CHKDOSFS -- Concurrent DOS disk lifecycle.
 * Lock ownership and process state are restored on normal exits. Native
 * writes require F; BDOS drive state is reset after a write attempt.
 */
#include <stdio.h>
#include "chkdosfs.h"
unsigned OSCALL(), KINIT(), KGETDP(), KOPEN(), KKEEP(), KERROR(), KREAD(), KWRITE();
static char queue[22]={0,0,0,0,0,0,0,0,'M','X','d','i','s','k',' ',' '};
static int held,kept,errmode,selected;
static unsigned drive,oldrive,spt;

diskclose()
{
    if(held) { OSCALL(139,queue); held=0; }
    if(wrote) OSCALL(37,1<<drive);
    if(errmode) { KERROR(0); errmode=0; }
    if(kept) { KKEEP(0); kept=0; }
    if(selected) { OSCALL(14,oldrive); selected=0; }
    return 0;
}

diskopen(d)
unsigned d;
{
    char dpb[29];
    unsigned v;
    v=OSCALL(12,0);
    if((v&0xfd00)!=0x1400 || OSCALL(163,0)!=0x1441) {
        printf("ERROR: CHKDOSFS requires Concurrent DOS 4.1.\n"); return 0;
    }
    oldrive=OSCALL(25,0); drive=d;
    selected=1;
    if(OSCALL(14,drive)&255) {
        printf("ERROR: Cannot select drive.\n"); diskclose(); return 0;
    }
    KINIT();
    if(KOPEN()) {
        printf("ERROR: Close open disk files before checking.\n"); diskclose(); return 0;
    }
    KKEEP(1); kept=1;
    if(OSCALL(135,queue) || OSCALL(137,queue)) {
        printf("ERROR: Cannot acquire MXdisk.\n"); diskclose(); return 0;
    }
    held=1;
    if(KOPEN()) {
        printf("ERROR: Open disk files detected after locking.\n"); diskclose(); return 0;
    }
    KERROR(1); errmode=1;
    if(!KGETDP(drive,dpb) || !geomset(dpb)) {
        printf("ERROR: Not a supported physical FAT12/FAT16 disk.\n");
        diskclose(); return 0;
    }
    spt=wordget(dpb+12);
    if(!spt || (vol.sectors-1)/spt>65535L) {
        printf("ERROR: Invalid track geometry.\n"); diskclose(); return 0;
    }
    return 1;
}

rdsect(sector,buf)
long sector;
char *buf;
{
    unsigned track,within;
    if(failed || !held || sector<0 || sector>=vol.sectors) return 0;
    track=sector/spt; within=sector%spt;
    if(KREAD(drive,track,within,buf)) {
        failed=1;
        printf("ERROR: Read error at sector %ld; check aborted.\n",sector);
        return 0;
    }
    return 1;
}

/* Enforce F at the physical write boundary, even if a higher layer errs. */
wrsect(sector,buf)
long sector;
char *buf;
{
    unsigned track,within;
    if(failed || !repair || !held || sector<0 || sector>=vol.sectors) return 0;
    track=sector/spt; within=sector%spt;
    wrote=1;
    if(KWRITE(drive,track,within,buf)) {
        failed=1;
        printf("ERROR: Write error at sector %ld; repair aborted.\n",sector);
        return 0;
    }
    return 1;
}
