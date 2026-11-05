/* Independent DR C adapter following Concurrent native P_CLI conventions.
 * Native resolver opens close before launch. DOS opens transfer only when
 * FMDOSOWN reports acceptance; the exclusive bridge then consumes them.
 */
#include "spawn.h"
int BDOS();
int FMLAUNCH();
int FMDOSOWN();
int FMORDER();
int FMSYSDISK();
static char *error;
char *fm_spawn_error() { return error ? error : ""; }
static int typeis(ext,s)
char *ext,*s;
{
    int i;
    for(i=0;i<3;++i) if((ext[i]&127)!=s[i]) return 0;
    return 1;
}
static int known(ext)
char *ext;
{
    return typeis(ext,"CMD") || typeis(ext,"BAT") ||
           typeis(ext,"COM") || typeis(ext,"EXE");
}
static int dos(ext)
char *ext;
{ return typeis(ext,"COM") || typeis(ext,"EXE"); }
static int parse(token,fcb)
char *token,*fcb;
{
    char expected[12],parsed[36],*packet[2];
    int i,j,c,base,ext,dot;
    for(i=0;i<12;++i) expected[i]=' ';
    expected[0]=0;i=0;
    if(token[0] && token[1]==':') {
        c=token[0];
        if(c<'A' || c>'P') return 0;
        expected[0]=c-'A'+1;i=2;
    }
    base=ext=dot=0;
    for(;token[i];++i) {
        c=token[i]&255;
        if(c<33 || c>126 || c==':' || c=='/' || c=='\\' ||
           c=='*' || c=='?' || c==';' || c==',' || c=='=' ||
           c=='<' || c=='>' || c=='|' || c=='"' || c=='[' || c==']' ||
           c=='!') return 0;
        if(c=='.') {if(dot || !base) return 0;dot=1;}
        else if(dot) {if(ext==3)return 0;expected[9+ext++]=c;}
        else {if(base==8)return 0;expected[1+base++]=c;}
    }
    if(!base || (dot && !ext)) return 0;
    for(j=0;j<36;++j) parsed[j]=fcb[j]=0;
    packet[0]=token;packet[1]=parsed;
    if(BDOS(152,packet)!=0) return 0;
    for(j=0;j<12;++j) if(parsed[j]!=expected[j]) return 0;
    for(j=0;j<12;++j) fcb[j]=expected[j];
    return 1;
}
static int openat(base,drive,user,fcb)
char *base,*fcb;int drive,user;
{
    int i,r;
    for(i=0;i<36;++i) fcb[i]=0;
    for(i=1;i<12;++i) fcb[i]=base[i];
    fcb[0]=drive;
    BDOS(32,user);
    r=BDOS(15,fcb);
    if((r&255)!=255) return 1;
    return (r&65535)==255 ? 0 : -1;
}
static int closeprog(fcb)
char *fcb;
{
    if((BDOS(16,fcb)&255)!=255) return 1;
    /* One cleanup retry after a failed close; never report launch success. */
    BDOS(16,fcb);
    return 0;
}
static int resolve(base,user,fcb,owner)
char *base,*fcb;int user,*owner;
{
    int r,sys;
    *owner=user;
    r=openat(base,base[0],user,fcb);
    if(r || base[0]) return r;
    sys=FMSYSDISK();
    if(sys<1 || sys>16) return 0;
    r=openat(base,sys,user,fcb);
    if(r<0) return -1;
    if(r) {
        if(fcb[10]&128) return 1;
        if(!closeprog(fcb)) return -1;
    }
    if(!user) return 0;
    r=openat(base,sys,0,fcb);
    if(r<0) return -1;
    if(r) {
        if(fcb[10]&128) {*owner=0;return 1;}
        if(!closeprog(fcb)) return -1;
    }
    return 0;
}
static int append(out,used,s)
char *out,*s;int *used;
{
    while(*s) {
        if(*used==127) return 0;
        out[(*used)++]=*s++;
    }
    out[*used]=0;
    return 1;
}
int fm_spawn(command,dma)
char *command,*dma;
{
    char token[15],base[36],fcb[36],order[13],line[128],name[15];
    char *p,*tail;
    int i,j,n,c,user,drive,owner,explicit,r,result,found,used,which,live,kind;
    error="Invalid command";result=live=kind=0;
    if(!dma) return 0;
    user=BDOS(32,255)&255;
    drive=(BDOS(25,0)&255)+1;
    BDOS(26,dma);
    if(!command) goto done;
    for(n=0;command[n] && n<=127;++n) ;
    error="Command exceeds 127 characters";
    if(n>127) goto done;
    p=command;
    while(*p==' ' || *p=='\t') ++p;
    error="Invalid executable name";
    for(n=0;p[n] && p[n]!=' ' && p[n]!='\t';++n) {
        if(n>=14) goto done;
        c=p[n]&255;if(c>='a' && c<='z') c=c-'a'+'A';token[n]=c;
    }
    if(!n) goto done;
    token[n]=0;tail=p+n;
    if(!parse(token,base)) goto done;
    explicit=base[9]!=' ';
    error="Unsupported executable type";
    if(explicit && !known(base+9)) goto done;
    for(i=0;i<13;++i) order[i]=0;
    order[0]=1;
    which=1;
    if(!explicit && FMORDER(order)==0) {
        error="Invalid program search order";
        for(i=0;i<4;++i) if(!known(order+1+i*3)) goto done;
        which=4;
    } else {
        order[1]='C';order[2]='M';order[3]='D';
    }
    found=0;
    for(i=0;i<which;++i) {
        if(!explicit) for(j=0;j<3;++j) base[9+j]=order[1+i*3+j];
        r=resolve(base,user,fcb,&owner);
        error="Cannot open or close program file";
        if(r<0) goto done;
        if(!r) continue;
        found=1;
        kind=dos(base+9);
        if(kind) live=1;
        else if(!closeprog(fcb)) goto done;
        break;
    }
    used=0;line[0]=0;
    error="Command exceeds 127 characters";
    if(found) {
        if(typeis(base+9,"BAT") && !append(line,&used,"BATCH ")) goto done;
        n=0;c=fcb[0]?fcb[0]:drive;
        if(c<1 || c>16) {error="Invalid program drive";goto done;}
        name[n++]='A'+c-1;name[n++]=':';
        for(j=1;j<9 && base[j]!=' ';++j) name[n++]=base[j];
        name[n++]='.';
        for(j=9;j<12 && base[j]!=' ';++j) name[n++]=base[j];
        name[n]=0;
        if(!append(line,&used,name)) goto done;
    } else {
        error="Program not found";
        if(explicit) goto done;
        owner=user;
        if(!append(line,&used,token)) {error="Command exceeds 127 characters";goto done;}
    }
    error="Command exceeds 127 characters";
    if(!append(line,&used,tail)) goto done;
    BDOS(32,owner);
    BDOS(26,dma);
    error="Cannot launch command";
    r=FMLAUNCH(line,kind,kind?fcb:0);
    if(kind && FMDOSOWN()) live=0;
    if(r!=0) goto done;
    /* A DOS success without acceptance violates the bridge contract. */
    if(live) goto done;
    error="";result=1;
done:
    if(live) {
        BDOS(32,owner);
        BDOS(26,dma);
        closeprog(fcb);
    }
    BDOS(32,user);
    BDOS(26,dma);
    return result;
}
