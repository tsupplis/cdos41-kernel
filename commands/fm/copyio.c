/* Original FM CODE 417F copies records through COPYTMP.$$$. This adapter
 * uses unused temporary names and a rollback backup so neither a failed copy
 * nor a failed commit deliberately discards an existing destination.
 * BDOS 22 and 23 must refuse collisions (as the target kernel does).
 */
#include "copyio.h"
int BDOS();
static char recovery[13];
char *fm_copy_recovery() { return recovery; }
int fm_copy_reset() { recovery[0]=0;return 0; }

static int fcbinit(fcb,drive,name)
char *fcb,*name;int drive;
{
    int i;
    for(i=0;i<36;++i) fcb[i]=0;
    fcb[0]=drive;
    for(i=0;i<11;++i) fcb[i+1]=name[i]&127;
    return 0;
}
static int validname(raw)
char *raw;
{
    int i,c,base,gap;
    base=gap=0;
    for(i=1;i<12;++i) {
        if(i==9) gap=0;
        c=raw[i]&127;
        if(c==' ') {gap=1;continue;}
        if(gap || c<33 || c>126 || c=='?' || c=='*' || c=='.' ||
           c==':' || c=='/' || c=='\\' || c==';' || c==',' ||
           c=='=' || c=='<' || c=='>' || c=='|' || c=='"' ||
           c=='[' || c==']') return 0;
        if(i<9) base=1;
    }
    return base;
}
/* 1 found, 0 absent, -1 search failure. Search DMA holds four entries. */
static int lookup(drive,user,name,buffer,ro)
int drive,user,*ro;char *name,*buffer;
{
    char fcb[36];int r;
    fcbinit(fcb,drive,name);
    BDOS(26,buffer);
    BDOS(32,user);
    r=BDOS(17,fcb);
    if((r&255)==255) return (r&65535)==255 ? 0 : -1;
    r=r&255;
    if(r>3) return -1;
    *ro=(buffer[r*32+9]&128)!=0;
    return 1;
}
static int same(a,b)
char *a,*b;
{
    int i;
    for(i=0;i<11;++i) if(a[i]!=b[i]) return 0;
    return 1;
}
static int normal(out,raw)
char *out,*raw;
{
    int i,c;
    for(i=0;i<11;++i) {
        c=raw[i+1]&127;
        if(c>='a' && c<='z') c=c-'a'+'A';
        out[i]=c;
    }
    return 0;
}
static int unused(drive,user,name,kind,buffer,target)
int drive,user,kind;char *name,*buffer,*target;
{
    int i,n,v,r,ro;
    for(n=0;n<256;++n) {
        name[0]='F';name[1]='M';name[2]='C';name[3]=kind;
        v=n;
        for(i=7;i>=4;--i) {name[i]='0'+v%10;v=v/10;}
        name[8]=name[9]=name[10]='$';
        if(same(name,target)) continue;
        r=lookup(drive,user,name,buffer,&ro);
        if(r<=0) return r==0;
    }
    return 0;
}
static int removefile(drive,user,name)
int drive,user;char *name;
{
    char fcb[36];
    fcbinit(fcb,drive,name);
    BDOS(32,user);
    return (BDOS(19,fcb)&255)!=255;
}
static int renamefile(drive,user,oldname,newname)
int drive,user;char *oldname,*newname;
{
    char fcb[36];int i;
    fcbinit(fcb,drive,oldname);
    fcb[16]=drive;
    for(i=0;i<11;++i) fcb[17+i]=newname[i];
    BDOS(32,user);
    return (BDOS(23,fcb)&255)!=255;
}
static int remember(name)
char *name;
{
    int i,n;
    n=0;
    for(i=0;i<8 && name[i]!=' ';++i) recovery[n++]=name[i];
    if(name[8]!=' ') {
        recovery[n++]='.';
        for(i=8;i<11 && name[i]!=' ';++i) recovery[n++]=name[i];
    }
    recovery[n]=0;
    return 0;
}
int fm_copy_users(sd,su,raw,dd,du,targetraw,dma,cancel)
int sd,su,dd,du;char *raw,*targetraw,*dma;int (*cancel)();
{
    char src[36],dst[36],source[11],name[11],temp[11],backup[11];
    char record[128];
    int result,r,ro,exists,sopen,dopen,own,backed,entryuser;
    recovery[0]=0;
    result=-1;sopen=dopen=own=backed=0;
    if(!dma) return -1;
    entryuser=BDOS(32,255)&255;
    if(su<0 || su>15 || du<0 || du>15) goto done;
    if(sd<1 || sd>16 || dd<1 || dd>16 || !raw || !targetraw)
        goto done;
    if(!validname(raw) || !validname(targetraw)) goto done;
    normal(source,raw);normal(name,targetraw);
    if(sd==dd && su==du && same(source,name)) goto done;
    exists=lookup(dd,du,name,record,&ro);
    if(exists<0 || (exists && ro)) goto done;
    if(!unused(dd,du,temp,'P',record,name)) goto done;
    if(exists && !unused(dd,du,backup,'B',record,name)) goto done;
    if(cancel && (*cancel)()) {result=0;goto done;}
    fcbinit(src,sd,source);
    BDOS(32,su);
    if((BDOS(15,src)&255)==255) goto done;
    sopen=1;
    fcbinit(dst,dd,temp);
    BDOS(32,du);
    if((BDOS(22,dst)&255)==255) goto done;
    dopen=own=1;
    for(;;) {
        if(cancel && (*cancel)()) {result=0;goto done;}
        BDOS(26,record);
        BDOS(32,su);
        r=BDOS(20,src)&255;
        if(r==1) break;
        if(r!=0) goto done;
        if(cancel && (*cancel)()) {result=0;goto done;}
        BDOS(26,record);
        BDOS(32,du);
        if((BDOS(21,dst)&255)!=0) goto done;
    }
    BDOS(32,su);
    if((BDOS(16,src)&255)==255) goto done;
    sopen=0;
    BDOS(32,du);
    if((BDOS(16,dst)&255)==255) goto done;
    dopen=0;
    if(cancel && (*cancel)()) {result=0;goto done;}
    /* Recheck before commit; a newly read-only target is never moved. */
    r=lookup(dd,du,name,record,&ro);
    if(r<0 || (r && ro) || r!=exists) goto done;
    if(exists) {
        if(!renamefile(dd,du,name,backup)) goto done;
        backed=1;
    }
    if(!renamefile(dd,du,temp,name)) {
        if(backed) {
            if(renamefile(dd,du,backup,name)) backed=0;
            else remember(backup);
        }
        goto done;
    }
    own=0;
    if(backed) {
        if(!removefile(dd,du,backup)) {remember(backup);goto done;}
        backed=0;
    }
    result=1;
done:
    /* Retry a failed close once on cleanup, never claim successful transfer. */
    if(sopen) {
        BDOS(32,su);
        if((BDOS(16,src)&255)==255) result=-1;
    }
    if(dopen) {
        BDOS(32,du);
        if((BDOS(16,dst)&255)==255) result=-1;
    }
    if(own && !removefile(dd,du,temp)) {
        if(!recovery[0]) remember(temp);
        result=-1;
    }
    BDOS(32,entryuser);
    BDOS(26,dma);
    return result;
}

/* Named copies use the caller's current user on both drives. */
int fm_copy_named(sd,raw,dd,targetraw,dma,cancel)
int sd,dd;char *raw,*targetraw,*dma;int (*cancel)();
{
    int user;
    user=BDOS(32,255)&255;
    return fm_copy_users(sd,user,raw,dd,user,targetraw,dma,cancel);
}

/* Historical same-name drive copy keeps the stricter same-drive refusal. */
int fm_copy_file(sd,raw,dd,dma,cancel)
int sd,dd;char *raw,*dma;int (*cancel)();
{
    if(sd==dd) {
        fm_copy_reset();
        if(dma) BDOS(26,dma);
        return -1;
    }
    return fm_copy_named(sd,raw,dd,raw,dma,cancel);
}
