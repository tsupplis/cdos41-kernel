/* CHKDOSFS -- allocation and directory checker.
 * Derived from the behaviour of the DOS Plus CHKDSK, not recovered source.
 * Cluster ownership is separate from FAT allocation. Marking every visited
 * cluster before following a link detects both cross-links and loops.
 * Directory state is iterative, keeping the native C stack bounded.
 */
#include <stdio.h>
#include "chkdosfs.h"
int strcmp();
static char owned[MAPSIZE], incoming[MAPSIZE], saved_owned[MAPSIZE];
static unsigned recovery_last;
static char dirbuf[SECSIZE], mirror[SECSIZE], entry[32];
static long dircache;
static unsigned framecl[MAXDEPTH], framesec[MAXDEPTH], frameidx[MAXDEPTH];
static unsigned framestop[MAXDEPTH];
static unsigned files, dirs, hidden, lost, freecnt, badcnt, chains;
static long filebytes;
static int repair_blocked,applying;
static unsigned fixes;

static marked(map,c)
char *map;
unsigned c;
{ return (map[c>>3] & (1<<(c&7)))!=0; }

static mark(map,c)
char *map;
unsigned c;
{ map[c>>3] |= 1<<(c&7); return 0; }

static valid(c)
unsigned c;
{ return c>=2 && c<vol.limit; }

static eof(c)
unsigned c;
{ return c>=(vol.fat16 ? 65528 : 4088); }

static issue(s,c)
char *s;
unsigned c;
{
    if(strcmp(s,"Lost clusters")) repair_blocked=1;
    printf("ERROR: %s: %u\n",s,c);
    if(errors!=65535) errors++;
    return 0;
}

/* Report a correction whose source chain is fully bounded by the ownership
 * scan. Preserve any unrelated blocker found earlier in that scan. */
static fixissue(s,c)
char *s;
unsigned c;
{
    int saved;
    if(applying) return 0;
    saved=repair_blocked;
    issue(s,c);
    repair_blocked=saved;
    fixes++;
    return 0;
}

static storelong(p,n)
char *p;
long n;
{
    int i;
    for(i=0;i<4;i++) { p[i]=n&255; n>>=8; }
    return 0;
}

/* Reread the directory sector before changing only this file's size field.
 * A directory buffer from an earlier parent/child visit may be stale. */
static filesize(sector,slot,size)
long sector,size;
unsigned slot;
{
    if(!rdsect(sector,mirror)) { failed=1; return 0; }
    storelong(mirror+slot*32+28,size);
    if(!wrsect(sector,mirror)) { failed=1; return 0; }
    dircache=-1L;
    return 1;
}

/* File chain scan. Bad/reserved/free links inside an allocated chain are
 * errors. Return 0xffffffff on a broken chain so file-size checks do not
 * report a misleading secondary error.
 */
static long filechain(c)
unsigned c;
{
    unsigned n;
    long count;
    count=0;
    while(!failed) {
        if(!valid(c)) { issue("Invalid cluster",c); return -1L; }
        if(marked(owned,c)) { issue("Cross-linked or looping chain",c); return -1L; }
        mark(owned,c); count++;
        n=fatget(c);
        if(failed) return -1L;
        if(eof(n)) return count;
        if(!valid(n)) {
            if(n==(vol.fat16 ? 65527 : 4087)) {
                issue("File uses bad cluster",c); return -1L;
            }
            fixissue("Broken cluster link",c);
            if(applying && !fatset(c,vol.fat16 ? 65535 : 4095)) {
                failed=1; return -1L;
            }
            return count;
        }
        c=n;
    }
    return -1L;
}

static printnam(e)
char *e;
{
    int i;
    for(i=0;i<8 && e[i]!=' ';i++) putchar(e[i]&255);
    if(e[8]!=' ') {
        putchar('.');
        for(i=8;i<11 && e[i]!=' ';i++) putchar(e[i]&255);
    }
    putchar('\n');
    return 0;
}

/* Every frame identifies one directory, its current chain cluster, physical
 * sector within that cluster, and entry slot. A zero-cluster frame is root.
 * End-of-directory stops entry interpretation but remaining directory-chain
 * clusters are still claimed and validated.
 */
static walkdir()
{
    int depth,i,oversized;
    unsigned c,n,slot,attr,start;
    long sector,size,count,needed;
    depth=0; framecl[0]=framesec[0]=frameidx[0]=framestop[0]=0;
    dircache=-1L;
    while(depth>=0 && !failed) {
        c=framecl[depth]; slot=frameidx[depth];
        if(!c) {
            if((long)framesec[depth]*16+slot>=vol.roots) { depth--; continue; }
            sector=vol.rootbase+framesec[depth];
        } else sector=vol.database+(long)(c-2)*vol.spc+framesec[depth];
        if(slot==16) {
            frameidx[depth]=0; framesec[depth]++;
            if(c && framesec[depth]==vol.spc) {
                framesec[depth]=0; n=fatget(c);
                if(failed) break;
                if(eof(n)) { depth--; continue; }
                if(!valid(n)) {
                    if(n==(vol.fat16 ? 65527 : 4087)) issue("Directory uses bad cluster",c);
                    else {
                        fixissue("Broken directory link",c);
                        if(applying && !fatset(c,vol.fat16 ? 65535 : 4095)) { failed=1; break; }
                    }
                    depth--; continue;
                }
                if(marked(owned,n)) { issue("Cross-linked or looping directory",n); depth--; continue; }
                mark(owned,n); framecl[depth]=n;
            }
            continue;
        }
        frameidx[depth]++;
        if(framestop[depth]) continue;
        if(sector!=dircache) {
            if(!rdsect(sector,dirbuf)) { failed=1; break; }
            dircache=sector;
        }
        for(i=0;i<32;i++) entry[i]=dirbuf[slot*32+i];
        if(entry[0]==0) { framestop[depth]=1; continue; }
        if((entry[0]&255)==229) continue;
        attr=entry[11]&255;
        if(attr==15) continue; /* VFAT long-name entries are not file owners. */
        if(entry[0]=='.' && (entry[1]==' ' || (entry[1]=='.' && entry[2]==' '))) continue;
        if(attr&8) continue;
        if(verbose) printnam(entry);
        start=wordget(entry+26); size=longget(entry+28);
        if(attr&16) {
            dirs++;
            if(!valid(start)) { issue("Invalid directory start",start); continue; }
            if(marked(owned,start)) { issue("Cross-linked directory",start); continue; }
            if(depth==MAXDEPTH-1) {
                printf("ERROR: Directory nesting exceeds checker limit; scan incomplete.\n");
                failed=1; break;
            }
            mark(owned,start); depth++;
            framecl[depth]=start;
            framesec[depth]=frameidx[depth]=framestop[depth]=0;
        } else {
            if(attr&2) hidden++; else files++;
            oversized=size<0 || size>vol.sectors*512L;
            if(oversized) {
                fixissue("File size exceeds volume",start);
                size=0;
            }
            if(size>2147483647L-filebytes) issue("File-size total overflow",start);
            else filebytes+=size;
            if(!start) {
                if(size || oversized) issue("Nonempty file has no cluster",start);
                continue;
            }
            count=filechain(start);
            if(count==-1L || failed) continue;
            needed=size/((long)vol.spc*512);
            if(size%((long)vol.spc*512)) needed++;
            if(count!=needed || oversized) {
                if(!oversized) fixissue("File size disagrees with chain",start);
                /* Original 0FB9h adjusts to the entire chain capacity; it
                 * does not discard excess clusters to match a smaller size. */
                if(applying && !filesize(sector,slot,count*vol.spc*512L)) break;
            }
        }
    }
    return !failed;
}

/* Compare all copies, including unused FAT tail bytes. No cache is dirtied. */
static mirrors()
{
    unsigned copy,sec,i;
    for(sec=0;sec<vol.fatsiz && !failed;sec++) {
        if(!rdsect(vol.fatbase+sec,dirbuf)) { failed=1; break; }
        for(copy=1;copy<vol.nfat && !failed;copy++) {
            if(!rdsect(vol.fatbase+(long)copy*vol.fatsiz+sec,mirror)) {
                failed=1; break;
            }
            for(i=0;i<SECSIZE;i++) if(dirbuf[i]!=mirror[i]) break;
            if(i<SECSIZE) issue("FAT copies differ at sector",sec);
        }
    }
    return !failed;
}

fscheck()
{
    unsigned c,n,i;
    for(i=0;i<MAPSIZE;i++) owned[i]=incoming[i]=0;
    errors=0;
    fatreset();
    repair_blocked=applying=0;
    fixes=0;
    files=dirs=hidden=lost=freecnt=badcnt=chains=0; filebytes=0;
    if(!mirrors() || !walkdir()) return 0;
    for(c=2;c<vol.limit && !failed;c++) {
        n=fatget(c);
        if(!n) freecnt++;
        else if(n==(vol.fat16 ? 65527 : 4087)) badcnt++;
        else if(!marked(owned,c)) {
            lost++;
            if(valid(n) && !marked(owned,n)) mark(incoming,n);
        }
    }
    if(failed) return 0;
    for(c=2;c<vol.limit;c++) {
        n=fatget(c);
        if(failed) return 0;
        if(n && n!=(vol.fat16 ? 65527 : 4087) &&
           !marked(owned,c) && !marked(incoming,c)) chains++;
    }
    if(lost) issue("Lost clusters",lost);
    printf("Files checked: %u  hidden files: %u  directories: %u\n",files,hidden,dirs);
    printf("%ld bytes in files\n",filebytes);
    printf("%ld bytes available, %ld bytes in bad clusters\n",
           (long)freecnt*vol.spc*512,
           (long)badcnt*vol.spc*512);
    if(lost) printf("%u lost-chain heads (cycles can have no head)\n",chains);
    printf("Consistency errors: %u\n",errors);
    if(!errors) printf("No inconsistencies found in checked entries.\n");
    else printf("Review the reported filesystem errors.\n");
    printf("Not checked: deleted entries, timestamps or file data sectors.\n");
    if(wrote) printf("Changes written.\n");
    else printf("No changes written.\n");
    return 1;
}

/* Count one orphan component, claiming each allocated cluster at most once.
 * Joins, cycles, invalid links and links into live files terminate at the last
 * unreferenced allocated cluster. Bad/free clusters are never adopted. */
static long orphanchain(c)
unsigned c;
{
    unsigned n;
    long count;
    count=0; recovery_last=0;
    while(valid(c) && !marked(owned,c)) {
        n=fatget(c);
        if(failed) return -1L;
        if(!n || n==(vol.fat16 ? 65527 : 4087)) break;
        mark(owned,c); recovery_last=c; count++;
        c=n;
    }
    return count;
}

static rootspace()
{
    unsigned index,slot,free;
    long sector;
    free=0; sector=-1L;
    for(index=0;index<vol.roots;index++) {
        if(sector!=vol.rootbase+(index>>4)) {
            sector=vol.rootbase+(index>>4);
            if(!rdsect(sector,dirbuf)) { failed=1; return 0; }
        }
        slot=(index&15)*32;
        if(!dirbuf[slot]) return free+vol.roots-index;
        if((dirbuf[slot]&255)==229) free++;
    }
    return free;
}

static rootname(name)
char *name;
{
    unsigned index,slot,i,c;
    long sector;
    sector=-1L;
    for(index=0;index<vol.roots;index++) {
        if(sector!=vol.rootbase+(index>>4)) {
            sector=vol.rootbase+(index>>4);
            if(!rdsect(sector,dirbuf)) { failed=1; return 1; }
        }
        slot=(index&15)*32;
        if(!dirbuf[slot]) return 0;
        if((dirbuf[slot]&255)==229) continue;
        for(i=0;i<11;i++) {
            c=dirbuf[slot+i]&255;
            if(c>='a' && c<='z') c-=32;
            if(c!=(name[i]&255)) break;
        }
        if(i==11) return 1;
    }
    return 0;
}

/* Match the original FILE%04xCHK convention, using uppercase FAT names and
 * incrementing the hexadecimal suffix if the generated name already exists. */
static recovered_file(head,count)
unsigned head;
long count;
{
    char name[11];
    unsigned id,index,slot,i,end;
    long tries,sector;
    id=head;
    for(tries=0;tries<65536L;tries++) {
        name[0]='F'; name[1]='I'; name[2]='L'; name[3]='E';
        for(i=0;i<4;i++) name[7-i]="0123456789ABCDEF"[(id>>(i*4))&15];
        name[8]='C'; name[9]='H'; name[10]='K';
        if(!rootname(name)) break;
        if(failed) return 0;
        id++;
    }
    if(tries==65536L) return 0;
    sector=-1L;
    for(index=0;index<vol.roots;index++) {
        if(sector!=vol.rootbase+(index>>4)) {
            sector=vol.rootbase+(index>>4);
            if(!rdsect(sector,dirbuf)) { failed=1; return 0; }
        }
        slot=(index&15)*32;
        end=dirbuf[slot]==0;
        if(!end && (dirbuf[slot]&255)!=229) continue;
        for(i=0;i<32;i++) dirbuf[slot+i]=0;
        for(i=0;i<11;i++) dirbuf[slot+i]=name[i];
        dirbuf[slot+26]=head; dirbuf[slot+27]=head>>8;
        storelong(dirbuf+slot+28,count*vol.spc*512L);
        /* Advancing an end marker must not expose stale records beyond it. */
        if(end && index+1<vol.roots) {
            if((index&15)!=15) dirbuf[slot+32]=0;
            else {
                if(!rdsect(sector+1,mirror)) { failed=1; return 0; }
                mirror[0]=0;
                if(!wrsect(sector+1,mirror)) { failed=1; return 0; }
            }
        }
        if(!wrsect(sector,dirbuf)) { failed=1; return 0; }
        printf("Recovered file: "); printnam(dirbuf+slot);
        return 1;
    }
    return 0;
}

static recoverfiles()
{
    unsigned c,i,pass,needed,n;
    long count;
    /* Preflight the entire orphan graph and directory capacity before any
     * writes. Preserve the original live-file ownership map for execution. */
    for(i=0;i<MAPSIZE;i++) saved_owned[i]=owned[i];
    needed=0;
    for(pass=0;pass<2 && !failed;pass++) {
        for(c=2;c<vol.limit && !failed;c++) {
            if(marked(owned,c) || (!pass && marked(incoming,c))) continue;
            count=orphanchain(c);
            if(count>0) needed++;
        }
    }
    for(i=0;i<MAPSIZE;i++) owned[i]=saved_owned[i];
    if(failed) return 0;
    if(rootspace()<needed || failed) {
        printf("ERROR: Root directory has insufficient free entries; recovery stopped.\n");
        return 0;
    }
    for(pass=0;pass<2 && !failed;pass++) {
        for(c=2;c<vol.limit && !failed;c++) {
            if(marked(owned,c) || (!pass && marked(incoming,c))) continue;
            count=orphanchain(c);
            if(count<0) return 0;
            if(!count) continue;
            n=fatget(recovery_last);
            if(failed) return 0;
            if(!eof(n) && !fatset(recovery_last,vol.fat16 ? 65535 : 4095)) return 0;
            if(!recovered_file(c,count)) return 0;
        }
    }
    return !failed;
}

/* A complete ownership scan precedes any writes. Correct sizes/EOF first,
 * verify, then recover or release orphan components. Uncertain ownership and
 * conflicting FAT copies block all changes. Data clusters are never rewritten.
 */
repairfs()
{
    unsigned c,n,released;
    if(repair_blocked) {
        printf("ERROR: Structural errors prevent lost-cluster repair; no changes written.\n");
        return 0;
    }
    if(fixes) {
        printf("Repair file sizes and end-of-file links (Y/N)? ");
        if(!confirm()) {
            printf("Repair cancelled; no changes written.\n"); return 1;
        }
        for(c=0;c<MAPSIZE;c++) owned[c]=0;
        applying=1;
        if(!walkdir()) {
            applying=0;
            printf("ERROR: Repair incomplete; disk may contain partial changes.\n"); return 0;
        }
        applying=0;
        if(!fscheck()) return 0;
        if(repair_blocked) {
            printf("ERROR: Verification found structural errors; repair stopped.\n"); return 0;
        }
    }
    if(!lost) return 1;
    printf("Convert lost chains to files (Y/N)? ");
    if(confirm()) {
        if(!recoverfiles()) {
            if(wrote) printf("ERROR: Recovery incomplete; disk may contain partial changes.\n");
            else printf("Recovery stopped; no changes written.\n");
            return 0;
        }
        return fscheck();
    }
    printf("Release %u unreferenced clusters (Y/N)? ",lost);
    if(!confirm()) {
        printf("Repair cancelled; no changes written.\n"); return 1;
    }
    released=0;
    for(c=2;c<vol.limit;c++) {
        if(marked(owned,c)) continue;
        n=fatget(c);
        if(failed) break;
        if(!n || n==(vol.fat16 ? 65527 : 4087)) continue;
        if(!fatset(c,0)) break;
        released++;
    }
    if(failed) {
        printf("ERROR: Repair incomplete; disk may contain partial changes.\n"); return 0;
    }
    printf("Released clusters: %u\n",released);
    return fscheck();
}
