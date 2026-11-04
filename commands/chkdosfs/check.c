/* CHKDOSFS -- report-only allocation and directory checker.
 * Derived from the behaviour of the DOS Plus CHKDSK, not recovered source.
 * Cluster ownership is separate from FAT allocation. Marking every visited
 * cluster before following a link detects both cross-links and loops.
 * Directory state is iterative, keeping the native C stack bounded.
 */
#include <stdio.h>
#include "chkdosfs.h"
static char owned[MAPSIZE], incoming[MAPSIZE];
static char dirbuf[SECSIZE], mirror[SECSIZE], entry[32];
static long dircache;
static unsigned framecl[MAXDEPTH], framesec[MAXDEPTH], frameidx[MAXDEPTH];
static unsigned framestop[MAXDEPTH];
static unsigned files, dirs, hidden, lost, freecnt, badcnt, chains;
static long filebytes;

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
    printf("ERROR: %s: %u\n",s,c);
    if(errors!=65535) errors++;
    return 0;
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
        if(!valid(n)) { issue("Broken cluster link",c); return -1L; }
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
    int depth,i;
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
                if(!valid(n)) { issue("Broken directory link",c); depth--; continue; }
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
            if(size<0 || size>vol.sectors*512L) {
                issue("File size exceeds volume",start);
                size=0;
            }
            if(size>2147483647L-filebytes) issue("File-size total overflow",start);
            else filebytes+=size;
            if(!start) {
                if(size) issue("Nonempty file has no cluster",start);
                continue;
            }
            count=filechain(start);
            if(count==-1L || failed) continue;
            needed=size/((long)vol.spc*512);
            if(size%((long)vol.spc*512)) needed++;
            if(count!=needed) issue("File size disagrees with chain",start);
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
    printf("No changes written.\n");
    return 1;
}
