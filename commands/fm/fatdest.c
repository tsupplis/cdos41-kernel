/* Use only public extended OPEN for mappings. FMLOC is a read-only view
 * of the current process's CAT/HDS. Extended CLOSE is not an unmap API,
 * so owned aliases remain process-local and are reclaimed at termination.
 */
#include "fatdest.h"
int BDOS();
int FMLOC();
static int owned[3];
static int protected_alias;
static int pinned[3];
static int signature[3][3];
static char *error;
char *fm_fat_destination_error()
{
    return error ? error : "";
}
static int valid(raw)
char *raw;
{
    int i,c,gap,base;
    if(!(raw[16]&64)) return 0;
    if((raw[1]&127)=='.') {
        c=raw[2]&127;
        if(c!='.' && c!=' ') return 0;
        for(i=3;i<12;++i) if((raw[i]&127)!=' ') return 0;
        return 1;
    }
    base=gap=0;
    for(i=1;i<12;++i) {
        if(i==9) gap=0;
        c=raw[i]&127;
        if(c==' ') {gap=1;continue;}
        if(gap || c<33 || c>126 || c=='.' || c=='?' || c=='*' ||
           c==':' || c=='/' || c=='\\' || c==';' || c==',' ||
           c=='=' || c=='<' || c=='>' || c=='|' || c=='"' ||
           c=='[' || c==']') return 0;
        if(i<9) base=1;
    }
    return base;
}
static int mapdir(source,raw,dma,allowsame)
int source,allowsame;char *raw,*dma;
{
    char fcb[36];
    int src[4],loc[4],i,j,alias,result,c;
    result=0;error="Invalid FAT directory";
    if(!dma) return 0;
    if(source<1 || source>16 || !raw) goto done;
    if(!valid(raw)) goto done;
    error="Cannot inspect source directory";
    if(!FMLOC(source,src) || src[0]<1 || src[0]>13) goto done;
    alias=0;
    for(i=0;i<3;++i) {
        if(i+14==source || i+14==protected_alias || pinned[i]) continue;
        error="Cannot inspect destination aliases";
        if(!FMLOC(i+14,loc)) goto done;
        if(owned[i]) {
            if(!loc[3] || loc[0]!=signature[i][0] ||
               loc[1]!=signature[i][1] || loc[2]!=signature[i][2])
                owned[i]=0;
        }
        if(!loc[3] || owned[i]) {alias=i+14;break;}
    }
    if(!alias) {error="No free destination alias (N:, O:, P:)";goto done;}
    for(j=0;j<36;++j) fcb[j]=0;
    fcb[0]=source|128;
    for(j=1;j<12;++j) {
        c=raw[j]&127;
        if(c>='a' && c<='z') c=c-'a'+'A';
        fcb[j]=c;
    }
    fcb[12]=alias-13;
    BDOS(26,dma);
    error="Cannot map destination directory";
    if((BDOS(15,fcb)&255)!=0) goto done;
    /* A successful map belongs to us, but never reuse it without a saved
     * identity. Failed verification leaves the mapping conservatively alone. */
    owned[i]=0;
    error="Cannot verify destination directory";
    if(!FMLOC(alias,loc) || !loc[3] || loc[0]<1 || loc[0]>13)
        goto done;
    owned[i]=1;
    for(j=0;j<3;++j) signature[i][j]=loc[j];
    if(!allowsame && loc[0]==src[0] && loc[2]==src[2]) {
        error="Destination is the source directory";result=-1;goto done;
    }
    error="";result=alias;
done:
    BDOS(26,dma);
    return result;
}

int fm_fat_destination(source,raw,dma)
int source;char *raw,*dma;
{
    return mapdir(source,raw,dma,0);
}
/* Capture may represent the current directory, unlike a copy destination. */
int fm_fat_capture(source,raw,dma)
int source;char *raw,*dma;
{
    return mapdir(source,raw,dma,1);
}
/* Read-only identity check; does not force a media login or directory read. */
int fm_fat_valid(alias)
int alias;
{
    int i,loc[4];
    error="Bookmark mapping is no longer available";
    if(alias<14 || alias>16) return 0;
    i=alias-14;
    if(!owned[i] || !FMLOC(alias,loc) || !loc[3]) return 0;
    if(loc[0]!=signature[i][0] || loc[1]!=signature[i][1] ||
       loc[2]!=signature[i][2]) {
        owned[i]=0;
        return 0;
    }
    error="";
    return 1;
}
int fm_fat_pin(alias)
int alias;
{
    if(!fm_fat_valid(alias)) return 0;
    pinned[alias-14]=1;
    return 1;
}
/* Unpin is local bookkeeping, including stale bookmarks; no disk change. */
int fm_fat_unpin(alias)
int alias;
{
    if(alias<14 || alias>16) return 0;
    pinned[alias-14]=0;
    return 1;
}
int fm_fat_same(source,alias)
int source,alias;
{
    int src[4],i;
    if(!fm_fat_valid(alias)) return 0;
    error="Cannot inspect source directory";
    if(source<1 || source>16 || !FMLOC(source,src) ||
       src[0]<1 || src[0]>13) return 0;
    error="";
    i=alias-14;
    return src[0]==signature[i][0] && src[2]==signature[i][2];
}
int fm_fat_clone(alias,dma)
int alias;char *dma;
{
    char raw[32];int i;
    if(!fm_fat_valid(alias)) {
        if(dma) BDOS(26,dma);
        return 0;
    }
    for(i=0;i<32;++i) raw[i]=0;
    for(i=1;i<12;++i) raw[i]=' ';
    raw[1]='.';raw[16]=64;
    return mapdir(alias,raw,dma,1);
}

/* Call immediately after intentional navigation, before identity validation.
 * This accepts a changed location only for our unpinned working aliases.
 */
int fm_fat_refresh_owned(alias)
int alias;
{
    int i,j,loc[4];
    error="Cannot refresh working directory alias";
    if(alias<14 || alias>16) return 0;
    i=alias-14;
    if(!owned[i] || pinned[i]) return 0;
    if(!FMLOC(alias,loc) || !loc[3] || loc[0]<1 || loc[0]>13)
        return 0;
    for(j=0;j<3;++j) signature[i][j]=loc[j];
    error="";
    return 1;
}

/* FIND_PATH (commands/d/path.a86) walks parents and finds each child by
 * cluster. Walk our scratch alias instead of overwriting saved kernel HDS
 * bytes as original FM CODE7113 did. Source and pinned aliases never move.
 */
static int root_path(source,path,capacity,dma)
int source,capacity;
char *path,*dma;
{
    char dot[32],fcb[36],record[128],tail[67],name[13];
    int original[4],loc[4],seen[33];
    int alias,user,i,j,n,used,depth,child,slot,found,result,cluster;
    char *entry;
    result=0;alias=0;used=0;depth=0;
    error="Invalid FAT path request";
    if(!path || capacity<4 || !dma || source<1 || source>16) return 0;
    path[0]=0;tail[0]=0;
    user=BDOS(32,255)&255;
    error="Cannot inspect source directory";
    if(!FMLOC(source,original) || original[0]<1 || original[0]>13)
        goto finish;
    for(i=0;i<32;++i) dot[i]=0;
    for(i=1;i<12;++i) dot[i]=' ';
    dot[1]='.';dot[16]=64;
    alias=fm_fat_capture(source,dot,dma);
    if(!alias) goto finish;
    BDOS(32,0);
    for(;;) {
        error="Cannot inspect path directory";
        if(!FMLOC(alias,loc) || !loc[3] || loc[0]!=original[0] ||
           loc[1]!=original[1]) goto finish;
        child=loc[2];
        if(!child) break;
        error="Invalid or excessive FAT directory depth";
        if(depth==33) goto finish;
        for(i=0;i<depth;++i) if(seen[i]==child) goto finish;
        seen[depth++]=child;
        for(i=0;i<36;++i) fcb[i]=0;
        for(i=1;i<12;++i) fcb[i]=' ';
        fcb[0]=alias|128;fcb[1]='.';fcb[2]='.';
        BDOS(26,record);
        error="Cannot read parent directory";
        if((BDOS(15,fcb)&255)!=0) goto finish;
        if(!fm_fat_refresh_owned(alias)) goto finish;
        error="Directory media changed during path lookup";
        if(!FMLOC(alias,loc) || loc[0]!=original[0] ||
           loc[1]!=original[1]) goto finish;
        for(i=0;i<36;++i) fcb[i]=0;
        for(i=1;i<12;++i) fcb[i]='?';
        fcb[0]=alias|128;
        slot=BDOS(17,fcb);found=0;
        for(;;) {
            error="Cannot find directory in parent";
            if((slot&255)==255) goto finish;
            if(slot<0 || slot>3) goto finish;
            entry=record+slot*32;
            cluster=(entry[26]&255)|((entry[27]&255)<<8);
            if((entry[16]&64) && cluster==child &&
               (entry[1]&127)!='.') {
                if(!valid(entry)) goto finish;
                n=0;
                for(i=1;i<9 && (entry[i]&127)!=' ';++i)
                    name[n++]=entry[i]&127;
                if((entry[9]&127)!=' ') {
                    name[n++]='.';
                    for(i=9;i<12 && (entry[i]&127)!=' ';++i)
                        name[n++]=entry[i]&127;
                }
                name[n]=0;found=1;break;
            }
            fcb[0]=alias|128;slot=BDOS(18,fcb);
        }
        error="FAT directory path is too long";
        j=n+(used?1:0);
        if(!found || used+j+3>66 || used+j+4>capacity) goto finish;
        for(i=used;i>=0;--i) tail[i+j]=tail[i];
        for(i=0;i<n;++i) tail[i]=name[i];
        if(used) tail[n]='\\';
        used+=j;
    }
    error="Source directory changed during path lookup";
    if(!FMLOC(source,loc)) goto finish;
    for(i=0;i<4;++i) if(loc[i]!=original[i]) goto finish;
    path[0]='A'+original[0]-1;path[1]=':';path[2]='\\';
    for(i=0;i<=used;++i) path[i+3]=tail[i];
    result=alias;error="";
finish:
    BDOS(32,user);BDOS(26,dma);
    return result;
}

/* Scoped exclusion prevents path discovery on a physical drive from reusing
 * its caller's active floating source. No ownership or pin state changes. */
int fm_fat_root_protected(source,path,capacity,dma,protect)
int source,capacity,protect;char *path,*dma;
{
    int previous,result;
    previous=protected_alias;protected_alias=protect;
    result=root_path(source,path,capacity,dma);
    protected_alias=previous;
    return result;
}
int fm_fat_root(source,path,capacity,dma)
int source,capacity;char *path,*dma;
{return fm_fat_root_protected(source,path,capacity,dma,0);}
