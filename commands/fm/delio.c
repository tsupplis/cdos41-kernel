/* Original FM: CODE 4FFE/1184. Use a fresh, concrete FCB; never clear
 * attributes, unlock files, retry, or expand wildcard names for deletion.
 */
#include "delio.h"
int BDOS();
int fm_delete_file(drive,raw)
int drive;
char *raw;
{
    char fcb[36];
    int i,c,base;
    if(drive<1 || drive>16 || !raw) return 0;
    for(i=0;i<36;++i) fcb[i]=0;
    fcb[0]=drive;
    base=0;
    for(i=1;i<12;++i) {
        c=raw[i]&127;
        if(c<32 || c==127 || c=='?' || c=='*' || c=='.' ||
           c==':' || c=='/' || c=='\\' || c==';' || c==',' ||
           c=='=' || c=='<' || c=='>' || c=='|' || c=='"' ||
           c=='[' || c==']') return 0;
        if(i<9 && c!=' ') base=1;
        fcb[i]=c;
    }
    if(!base) return 0;
    return (BDOS(19,fcb)&255)!=255;
}
