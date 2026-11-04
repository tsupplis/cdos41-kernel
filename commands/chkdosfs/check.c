/* CHKDOSFS -- allocation and directory checker.
 * Derived from the behaviour of the DOS Plus CHKDSK, not recovered source.
 * Cluster ownership is separate from FAT allocation. Marking every visited
 * cluster before following a link detects both cross-links and loops.
 * Directory state is iterative, keeping the native C stack bounded.
 */
#include <stdio.h>
#include "chkdosfs.h"
int strcmp();
static char owned[MAPSIZE], incoming[MAPSIZE], workmap[MAPSIZE];
static unsigned recovery_last;
static char dirbuf[SECSIZE], mirror[SECSIZE], entry[32];
static long dircache;
static unsigned framehead[MAXDEPTH];
static unsigned framecl[MAXDEPTH], framesec[MAXDEPTH], frameidx[MAXDEPTH];
static unsigned framestop[MAXDEPTH];
static unsigned files, dirs, hidden, lost, freecnt, badcnt, chains;
static long filebytes,data_sectors,user_alloc,hidden_alloc,directory_alloc;
static char readbuf[SECSIZE];
static int repair_blocked,applying;
static unsigned fixes;
#define MAXRECOVERDIR 256
static unsigned directory_heads[MAXRECOVERDIR], saved_heads[MAXRECOVERDIR];
static unsigned directory_count;
static int probing_directory;
#define MAXCONTIG 256
struct contiguous_plan {
    long sector,bytes;
    unsigned slot,start,count;
};
static struct contiguous_plan contiguous[MAXCONTIG];
static unsigned contiguous_count;
/* workmap is phase-local scratch: proposed L ranges, or an ownership
 * backup during orphan recovery. Each phase initializes it completely. */

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

/* Keep a validated repair candidate distinct from an ownership blocker. */
static repair_note(s,c)
char *s;
unsigned c;
{
    int saved;
    saved=repair_blocked;
    issue(s,c);
    repair_blocked=saved;
    return 0;
}

static fixissue(s,c)
char *s;
unsigned c;
{
    if(applying) return 0;
    repair_note(s,c);
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

/* B reads complete referenced clusters, including slack, into a separate
 * buffer so directory/cache state is never overwritten by file contents.
 * It neither marks bad clusters nor invents replacement data. Every read
 * failure invalidates the current repair preflight immediately. */
static read_cluster(cluster)
unsigned cluster;
{
    unsigned off;
    long sector;
    if(!valid(cluster)) { failed=1; return 0; }
    for(off=0;off<vol.spc;off++) {
        sector=vol.database+(long)(cluster-2)*vol.spc+off;
        if(!rdsect(sector,readbuf)) {
            printf("ERROR: Data read test failed at cluster %u.\n",cluster);
            failed=1; return 0;
        }
        data_sectors++;
    }
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
        if(read_file_data && n!=(vol.fat16 ? 65527 : 4087) && !read_cluster(c)) return -1L;
        if(eof(n)) return count;
        if(!valid(n)) {
            if(n==(vol.fat16 ? 65527 : 4087)) {
                issue("File uses bad cluster",c); return -1L;
            }
            if(rebuild_contiguous) { issue("Broken cluster link",c); return -1L; }
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

/* Original CODE 0D23h reports the volume label and its DOS timestamp.
 * Bound the name and validate date fields before formatting; never index an
 * unchecked on-disk month into the original's month-name pointer table. */
static volume_label(e)
char *e;
{
    char name[12];
    unsigned i,last,c,date,time,year,month,day,hour,minute;
    last=0;
    for(i=0;i<11;i++) {
        c=e[i]&255;
        name[i]=(c<32 || c==127) ? '?' : c;
        if(c!=' ') last=i+1;
    }
    name[last]=0;
    printf("Volume %s",name);
    date=wordget(e+24); time=wordget(e+22);
    year=1980+(date>>9); month=(date>>5)&15; day=date&31;
    hour=time>>11; minute=(time>>5)&63;
    if(month>=1 && month<=12 && day>=1 && day<=31 && hour<24 && minute<60)
        printf(" created %u-%02u-%02u %u:%02u",year,month,day,hour,minute);
    else printf(" (timestamp absent or invalid)");
    putchar('\n');
    return 0;
}

/* L uses the historical adjacent-entry/free-FAT heuristic. It deliberately
 * skips the last entry of a directory cache cluster, like the original.
 * Candidate tails are not claimed until all live references have been read. */
static contiguous_candidate(sector,slot,relative,root,start,size)
long sector,size;
unsigned slot,relative,root,start;
{
    char *next;
    unsigned c,n;
    long need;
    struct contiguous_plan *p;
    if(size<=0 || size>vol.sectors*512L || !valid(start)) return 0;
    need=size/((long)vol.spc*512);
    if(size%((long)vol.spc*512)) need++;
    if(need<=0 || need>=(long)(vol.limit-start)) return 0;
    if(root && (long)relative*16+slot+1>=vol.roots) return 0;
    if(slot==15) {
        if((relative+1)%vol.spc==0) return 0;
        if(!rdsect(sector+1,mirror)) { failed=1; return 0; }
        next=mirror;
    } else next=dirbuf+(slot+1)*32;
    if(!next[0] || (next[0]&255)==229 || next[0]=='.' || (next[11]&8)) return 0;
    if(wordget(next+26)!=start+(unsigned)need) return 0;
    for(c=start;c<start+(unsigned)need;c++) {
        n=fatget(c);
        if(failed || n) return 0;
    }
    if(contiguous_count==MAXCONTIG) {
        printf("ERROR: Too many contiguous-chain candidates; scan stopped.\n");
        failed=1; return 0;
    }
    p=&contiguous[contiguous_count++];
    p->sector=sector; p->slot=slot; p->start=start;
    p->bytes=size; p->count=(unsigned)need;
    repair_note("Missing contiguous file chain",start);
    return 1;
}

/* Validate every range against the completed ownership scan and against the
 * other proposed ranges. Recheck the file/adjacent entries and all FAT values
 * before any repair writes, including after the user's confirmation. */
static contiguous_preflight()
{
    unsigned i,c,last;
    char *e;
    struct contiguous_plan *p;
    for(i=0;i<MAPSIZE;i++) workmap[i]=0;
    for(i=0;i<contiguous_count;i++) {
        p=&contiguous[i];
        if(!rdsect(p->sector,mirror)) { failed=1; return 0; }
        e=mirror+p->slot*32;
        if(!e[0] || (e[0]&255)==229 || (e[11]&24) ||
           wordget(e+26)!=p->start || longget(e+28)!=p->bytes) {
            issue("Contiguous candidate changed",p->start); return 0;
        }
        if(p->slot==15) {
            if(!rdsect(p->sector+1,mirror)) { failed=1; return 0; }
            e=mirror;
        } else e+=32;
        if(!e[0] || (e[0]&255)==229 || e[0]=='.' || (e[11]&8) ||
           wordget(e+26)!=p->start+p->count) {
            issue("Contiguous boundary changed",p->start); return 0;
        }
        /* Never activate a file through a head entry that needs two sector
         * writes. It remains detectable, but cannot be committed indivisibly. */
        if(!vol.fat16 && ((((long)p->start*3)>>1)&511)==511) {
            issue("Contiguous start spans FAT sectors; detection only",p->start);
            return 0;
        }
        last=p->start+p->count;
        for(c=p->start;c<last;c++) {
            if((c!=p->start && marked(owned,c)) || marked(workmap,c)) {
                issue("Conflicting contiguous ownership",c); return 0;
            }
            if(fatget(c)!=0 || failed) {
                if(!failed) issue("Contiguous range is not free",c);
                return 0;
            }
            mark(workmap,c);
            if(read_file_data && !read_cluster(c)) return 0;
        }
    }
    return !repair_blocked;
}

/* R only reconnects allocated first-level directories. Existing dot entries,
 * including the root parent pointer, must already be valid; never rewrite them. */
static directory_header(head,parent)
unsigned head,parent;
{
    unsigned i;
    char *dot,*up;
    if(!rdsect(vol.database+(long)(head-2)*vol.spc,mirror)) { failed=1; return 0; }
    dot=".          "; up="..         ";
    for(i=0;i<11;i++) if(mirror[i]!=dot[i] || mirror[32+i]!=up[i]) return 0;
    if(!(mirror[11]&16) || !(mirror[43]&16) || (mirror[11]&0xc8) || (mirror[43]&0xc8)) return 0;
    return wordget(mirror+26)==head && wordget(mirror+58)==parent &&
           longget(mirror+28)==0 && longget(mirror+60)==0;
}

static valid_recovered_name(name)
char *name;
{
    unsigned i,c,space;
    char *bad;
    if(name[0]==' ') return 0;
    space=0;
    for(i=0;i<11;i++) {
        if(i==8) space=0;
        c=name[i]&255;
        if(c==' ') { space=1; continue; }
        if(space || (c<32 && !(i==0 && c==5)) || c==127) return 0;
        for(bad="\"*+,./:;<=>?[\\]|";*bad;bad++) if(c==(*bad&255)) return 0;
    }
    return 1;
}

/* Check earlier records of this directory for case-insensitive duplicate
 * short names. No extra namespace or data is exposed when evidence conflicts. */
static unique_recovered_name(head,target,slot,name)
unsigned head,slot;
long target;
char *name;
{
    unsigned c,off,j,i,a,b,hops;
    long sector;
    c=head; hops=0;
    while(valid(c) && hops++<vol.limit) {
        for(off=0;off<vol.spc;off++) {
            sector=vol.database+(long)(c-2)*vol.spc+off;
            if(!rdsect(sector,mirror)) { failed=1; return 0; }
            for(j=0;j<16;j++) {
                if(sector==target && j==slot) return 1;
                if(!mirror[j*32]) return 0;
                if((mirror[j*32]&255)==229 || (mirror[j*32+11]&255)==15) continue;
                for(i=0;i<11;i++) {
                    a=mirror[j*32+i]&255; b=name[i]&255;
                    if(a>='a' && a<='z') a-=32;
                    if(b>='a' && b<='z') b-=32;
                    if(a!=b) break;
                }
                if(i==11) return 0;
            }
        }
        c=fatget(c);
        if(failed) return 0;
    }
    return 0;
}

/* Every frame identifies one directory, its current chain cluster, physical
 * sector within that cluster, and entry slot. A zero-cluster frame is root.
 * End-of-directory stops entry interpretation but remaining directory-chain
 * clusters are still claimed and validated.
 */
static walkdir(head)
unsigned head;
{
    int depth,i,oversized;
    unsigned c,n,slot,attr,start;
    long sector,size,count,needed;
    depth=0; framehead[0]=framecl[0]=head;
    framesec[0]=frameidx[0]=framestop[0]=0;
    dircache=-1L;
    while(depth>=0 && !failed) {
        c=framecl[depth]; slot=frameidx[depth];
        if(read_file_data && c && !slot && !framesec[depth] && !read_cluster(c)) break;
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
                    else if(rebuild_contiguous) issue("Broken directory link",c);
                    else {
                        fixissue("Broken directory link",c);
                        if(applying && !fatset(c,vol.fat16 ? 65535 : 4095)) { failed=1; break; }
                    }
                    depth--; continue;
                }
                if(marked(owned,n)) { issue("Cross-linked or looping directory",n); depth--; continue; }
                mark(owned,n); directory_alloc+=(long)vol.spc*512; framecl[depth]=n;
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
        if(entry[0]=='.' && (entry[1]==' ' || (entry[1]=='.' && entry[2]==' '))) {
            if(probing_directory && (c!=framehead[depth] || framesec[depth]!=0 ||
               !((slot==0 && entry[1]==' ') || (slot==1 && entry[1]=='.')))) {
                issue("Invalid recovered dot-entry position",c); return 0;
            }
            continue;
        }
        if(attr&8) {
            if(probing_directory) { issue("Invalid recovered directory attribute",c); return 0; }
            volume_label(entry);
            continue;
        }
        if(probing_directory && ((attr&0xc0) || ((attr&16) && longget(entry+28)!=0))) {
            issue("Invalid recovered directory record",c); return 0;
        }
        if(probing_directory && (!valid_recovered_name(entry) ||
           !unique_recovered_name(framehead[depth],sector,slot,entry))) {
            if(!failed) issue("Invalid or duplicate recovered filename",framehead[depth]);
            return 0;
        }
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
            if(probing_directory && !directory_header(start,framehead[depth])) {
                if(!failed) issue("Invalid recovered directory parent",start);
                return 0;
            }
            mark(owned,start); directory_alloc+=(long)vol.spc*512; depth++;
            framehead[depth]=framecl[depth]=start;
            framesec[depth]=frameidx[depth]=framestop[depth]=0;
        } else {
            if(attr&2) hidden++; else files++;
            oversized=size<0 || size>vol.sectors*512L;
            if(oversized) {
                if(rebuild_contiguous) issue("File size exceeds volume",start);
                else fixissue("File size exceeds volume",start);
                size=0;
            }
            if(size>2147483647L-filebytes) issue("File-size total overflow",start);
            else filebytes+=size;
            if(!start) {
                if(size || oversized) issue("Nonempty file has no cluster",start);
                continue;
            }
            if(rebuild_contiguous && valid(start) && fatget(start)==0 && !failed) {
                if(marked(owned,start)) { issue("Cross-linked file start",start); continue; }
                mark(owned,start);
                if(!contiguous_candidate(sector,slot,framesec[depth],c==0,start,size) && !failed)
                    issue("Insufficient contiguous-chain evidence",start);
                continue;
            }
            count=filechain(start);
            if(count==-1L || failed) continue;
            if(attr&2) hidden_alloc+=count*vol.spc*512L;
            else user_alloc+=count*vol.spc*512L;
            needed=size/((long)vol.spc*512);
            if(size%((long)vol.spc*512)) needed++;
            if(count!=needed || oversized) {
                if(rebuild_contiguous) { issue("File size disagrees with chain",start); continue; }
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

/* D is diagnostic, even with F. Deleted directories may leave dot entries
 * in free clusters after their allocation links and parent entry are gone.
 * Compare distinct entries (the original compared the same entry twice),
 * require plausible attributes/self/parent fields, and never claim or alter
 * those free clusters. A read failure invalidates the complete repair scan.
 */
static erased_directories()
{
    unsigned c,n,i,found,parent;
    char *dot,*up;
    found=0; dot=".          "; up="..         ";
    for(c=2;c<vol.limit;c++) {
        if(marked(owned,c)) continue;
        n=fatget(c);
        if(failed) return 0;
        if(n) continue;
        if(!rdsect(vol.database+(long)(c-2)*vol.spc,dirbuf)) {
            failed=1; return 0;
        }
        for(i=0;i<11;i++) if(dirbuf[i]!=dot[i] || dirbuf[32+i]!=up[i]) break;
        if(i!=11) continue;
        if(!(dirbuf[11]&16) || !(dirbuf[43]&16) ||
           (dirbuf[11]&8) || (dirbuf[43]&8)) continue;
        if(wordget(dirbuf+26)!=c || longget(dirbuf+28)!=0 ||
           longget(dirbuf+60)!=0) continue;
        parent=wordget(dirbuf+58);
        if(parent && (!valid(parent) || parent==c)) continue;
        printf("Erased directory remnant at cluster %u\n",c);
        found++;
    }
    printf("Erased directory remnants: %u\n",found);
    return 1;
}

/* Validate all candidate trees against live ownership and one another before
 * changing any namespace. Restore reporting counters and live ownership after
 * probing. The normal walk never applies fixes while this flag is set. */
static orphan_directories()
{
    unsigned c,i,n,old_files,old_dirs,old_hidden,old_fixes,old_errors;
    long old_bytes,old_user,old_hidden_alloc,old_directory;
    int old_l,old_applying,ok;
    old_files=files; old_dirs=dirs; old_hidden=hidden; old_bytes=filebytes;
    old_user=user_alloc; old_hidden_alloc=hidden_alloc; old_directory=directory_alloc;
    old_fixes=fixes; old_l=rebuild_contiguous; old_applying=applying; applying=0;
    rebuild_contiguous=0; probing_directory=1; directory_count=0;
    for(i=0;i<MAPSIZE;i++) workmap[i]=owned[i];
    for(c=2;c<vol.limit && !failed;c++) {
        if(marked(owned,c)) continue;
        n=fatget(c);
        if(failed) break;
        if(!n || n==(vol.fat16 ? 65527 : 4087)) continue;
        if(!directory_header(c,0)) continue;
        if(directory_count==MAXRECOVERDIR) {
            printf("ERROR: Too many directory candidates; scan stopped.\n"); failed=1; break;
        }
        old_errors=errors; mark(owned,c);
        ok=walkdir(c);
        if(!ok || errors!=old_errors) {
            repair_blocked=1;
            printf("Directory candidate rejected at cluster %u\n",c);
            break;
        }
        directory_heads[directory_count++]=c;
        printf("Orphaned first-level directory at cluster %u\n",c);
    }
    for(i=0;i<MAPSIZE;i++) owned[i]=workmap[i];
    files=old_files; dirs=old_dirs; hidden=old_hidden; filebytes=old_bytes;
    user_alloc=old_user; hidden_alloc=old_hidden_alloc; directory_alloc=old_directory;
    fixes=old_fixes; rebuild_contiguous=old_l; applying=old_applying; probing_directory=0;
    printf("Directory recovery candidates: %u\n",directory_count);
    return !failed && !repair_blocked;
}

fscheck()
{
    unsigned c,n,i;
    for(i=0;i<MAPSIZE;i++) owned[i]=incoming[i]=0;
    errors=0; data_sectors=0;
    fatreset();
    repair_blocked=applying=0;
    fixes=contiguous_count=0;
    files=dirs=hidden=lost=freecnt=badcnt=chains=0; filebytes=0;
    user_alloc=hidden_alloc=directory_alloc=0;
    if(!mirrors() || !walkdir(0)) return 0;
    if(rebuild_contiguous) {
        contiguous_preflight();
        if(failed) return 0;
        printf("Contiguous-chain candidates: %u\n",contiguous_count);
    }
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
    if(scan_erased && !erased_directories()) return 0;
    if(recover_directories) {
        orphan_directories();
        if(failed) return 0;
    }
    printf("Files checked: %u  hidden files: %u  directories: %u\n",files,hidden,dirs);
    printf("%ld bytes in files\n",filebytes);
    printf("%ld bytes allocated: files %ld, hidden %ld, directories %ld\n",
           user_alloc+hidden_alloc+directory_alloc,user_alloc,hidden_alloc,directory_alloc);
    printf("%ld bytes total disk space\n",(long)(vol.limit-2)*vol.spc*512);
    printf("%ld bytes available, %ld bytes in bad clusters\n",
           (long)freecnt*vol.spc*512,
           (long)badcnt*vol.spc*512);
    if(lost) printf("%u lost-chain heads (cycles can have no head)\n",chains);
    printf("Consistency errors: %u\n",errors);
    if(!errors) printf("No inconsistencies found in checked entries.\n");
    else printf("Review the reported filesystem errors.\n");
    if(read_file_data) {
        printf("File/directory data sectors read: %ld\n",data_sectors);
        printf("Not checked: deleted entries, timestamps or free-space surface.\n");
    } else printf("Not checked: deleted entries, timestamps or file data sectors.\n");
    if(wrote) printf("Changes written.\n");
    else printf("No changes written.\n");
    return 1;
}

/* Verification failure must not be mistaken for successful or read-only
 * completion after metadata was already written. */
static verify_changes()
{
    if(fscheck()) return 1;
    if(wrote) printf("ERROR: Repair could not be verified; disk may contain partial changes.\n");
    return 0;
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
        if(read_file_data && !read_cluster(c)) return -1L;
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
static recovered_file(head,count,as_directory)
unsigned head;
long count;
int as_directory;
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
        dirbuf[slot+11]=as_directory ? 16 : 32;
        dirbuf[slot+26]=head; dirbuf[slot+27]=head>>8;
        storelong(dirbuf+slot+28,as_directory ? 0L : count*vol.spc*512L);
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
        printf(as_directory ? "Recovered directory: " : "Recovered file: "); printnam(dirbuf+slot);
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
    for(i=0;i<MAPSIZE;i++) workmap[i]=owned[i];
    needed=0;
    for(pass=0;pass<2 && !failed;pass++) {
        for(c=2;c<vol.limit && !failed;c++) {
            if(marked(owned,c) || (!pass && marked(incoming,c))) continue;
            count=orphanchain(c);
            if(count>0) needed++;
        }
    }
    for(i=0;i<MAPSIZE;i++) owned[i]=workmap[i];
    if(failed) return 0;
    i=rootspace();
    if(failed) return 0;
    if(i<needed) {
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
            if(!recovered_file(c,count,0)) return 0;
        }
    }
    return !failed;
}

static cancelled_repair()
{
    if(wrote) printf("Further recovery cancelled; previous changes retained.\n");
    else printf("Repair cancelled; no changes written.\n");
    return 1;
}

/* R writes new root entries only. Candidate trees, FAT chains, dot entries,
 * child metadata and data remain unchanged. Declining never frees anything. */
static recoverdirs()
{
    unsigned i,expected,free;
    expected=directory_count;
    if(!expected) return 1;
    free=rootspace();
    if(failed) return 0;
    if(free<expected) { printf("ERROR: Root directory has insufficient free entries; recovery stopped.\n"); return 0; }
    for(i=0;i<expected;i++) saved_heads[i]=directory_heads[i];
    printf("Recover validated first-level directories (Y/N)? ");
    if(!confirm()) return cancelled_repair();
    if(!orphan_directories()) return 0;
    if(directory_count!=expected) { issue("Directory candidates changed",directory_count); return 0; }
    for(i=0;i<expected;i++) if(directory_heads[i]!=saved_heads[i]) {
        issue("Directory candidates changed",directory_heads[i]); return 0;
    }
    free=rootspace();
    if(failed) return 0;
    if(free<expected) { issue("Root directory capacity changed",free); return 0; }
    for(i=0;i<expected;i++) {
        if(!recovered_file(directory_heads[i],0L,1)) {
            printf("ERROR: Directory recovery incomplete; disk may contain partial changes.\n");
            return 0;
        }
    }
    return verify_changes();
}

/* A complete ownership scan precedes any writes. Correct sizes/EOF first,
 * verify, then recover or release orphan components. Uncertain ownership and
 * conflicting FAT copies block all changes. Data clusters are never rewritten.
 */
repairfs()
{
    unsigned c,n,released;
    if(repair_blocked) {
        printf("ERROR: Unresolved safety checks prevent repair; no changes written.\n");
        return 0;
    }
    if(recover_directories && directory_count) {
        released=rootspace();
        if(failed) return 0;
        if(released<directory_count) {
            printf("ERROR: Root directory has insufficient free entries; recovery stopped.\n"); return 0;
        }
    }
    if(rebuild_contiguous && contiguous_count) {
        printf("Rebuild candidate contiguous file chains (Y/N)? ");
        if(!confirm()) {
            return cancelled_repair();
        }
        if(!contiguous_preflight()) return 0;
        for(n=0;n<contiguous_count;n++) {
            /* Commit the starting link last, after its complete tail exists. */
            c=contiguous[n].start+contiguous[n].count-1;
            while(1) {
                if(!fatset(c,c==contiguous[n].start+contiguous[n].count-1 ?
                           (vol.fat16 ? 65535 : 4095) : c+1)) {
                    failed=1;
                    printf("ERROR: Repair incomplete; disk may contain partial changes.\n"); return 0;
                }
                if(c==contiguous[n].start) break;
                c--;
            }
        }
        if(!verify_changes()) return 0;
        if(repair_blocked) return 0;
    }
    if(fixes) {
        printf("Repair file sizes and end-of-file links (Y/N)? ");
        if(!confirm()) {
            return cancelled_repair();
        }
        for(c=0;c<MAPSIZE;c++) owned[c]=0;
        applying=1;
        if(!walkdir(0)) {
            applying=0;
            printf("ERROR: Repair incomplete; disk may contain partial changes.\n"); return 0;
        }
        applying=0;
        if(!verify_changes()) return 0;
        if(repair_blocked) {
            printf("ERROR: Verification found structural errors; repair stopped.\n"); return 0;
        }
    }
    if(recover_directories) return recoverdirs();
    if(!lost) return 1;
    printf("Convert lost chains to files (Y/N)? ");
    if(confirm()) {
        if(!recoverfiles()) {
            if(wrote) printf("ERROR: Recovery incomplete; disk may contain partial changes.\n");
            else printf("Recovery stopped; no changes written.\n");
            return 0;
        }
        return verify_changes();
    }
    printf("Release %u unreferenced clusters (Y/N)? ",lost);
    if(!confirm()) {
        return cancelled_repair();
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
    return verify_changes();
}
