/* Original FM: CODE 4E24/11C5. Unlike its permissive parser, this adapter
 * deliberately disallows wildcard mutations and accepts one bare 8.3 name.
 * BDOS 23 refuses collisions; never delete or overwrite the destination.
 */
#include "renio.h"
int BDOS();
int fm_rename_file(drive,raw,text,dma,newraw)
int drive;
char *raw,*text,*dma,*newraw;
{
    char name[13],expected[11],parsed[36],fcb[36],*packet[2];
    int i,n,base,ext,dot,c,result;
    if(drive<1 || drive>16 || !raw || !text || !dma || !newraw)
        return 0;
    for(i=0;i<11;++i) expected[i]=' ';
    base=ext=dot=0;
    for(n=0;text[n];++n) {
        if(n>=12) return 0;
        c=text[n]&255;
        if(c<33 || c>126 || c==':' || c=='/' || c=='\\' ||
           c=='*' || c=='?' || c==';' || c==',' || c=='=' ||
           c=='<' || c=='>' || c=='|' || c=='"' || c=='[' || c==']')
            return 0;
        if(c>='a' && c<='z') c=c-'a'+'A';
        name[n]=c;
        if(c=='.') {
            if(dot || !base) return 0;
            dot=1;
        } else if(dot) {
            if(ext>=3) return 0;
            expected[8+ext++]=c;
        } else {
            if(base>=8) return 0;
            expected[base++]=c;
        }
    }
    if(!base || (dot && !ext)) return 0;
    name[n]=0;
    for(i=0;i<36;++i) parsed[i]=fcb[i]=0;
    packet[0]=name;packet[1]=parsed;
    /* Nonzero F_PARSE return is an error or an unconsumed input pointer. */
    if(BDOS(152,packet)!=0 || parsed[0]!=0) return 0;
    for(i=0;i<11;++i)
        if(parsed[i+1]!=expected[i]) return 0;
    fcb[0]=drive;fcb[16]=drive;
    for(i=1;i<12;++i) {
        fcb[i]=raw[i]&127;
        if(fcb[i]=='?' || fcb[i]=='*') return 0;
        fcb[i+16]=expected[i-1];
    }
    result=BDOS(23,fcb);
    if((result&255)==255) return (result&65535)==0x08ff ? -2 : -1;
    for(i=0;i<32;++i) newraw[i]=raw[i];
    for(i=1;i<12;++i) newraw[i]=(raw[i]&128)|expected[i-1];
    return 1;
}
