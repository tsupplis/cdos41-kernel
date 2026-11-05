/* Named-copy selection loop. Concrete targets are encoded locally so a
 * parser cannot expand wildcards or silently accept a partial filename.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "copynam.h"
static int lastdrive;
int fm_copy_name_drive() { return lastdrive; }
static int target_name(text,source,raw)
char *text,*raw;
int source;
{
    int i,c,drive,base,ext,dot;
    for(i=0;i<32;++i) raw[i]=0;
    for(i=1;i<12;++i) raw[i]=' ';
    drive=source;i=0;
    if(text[0] && text[1]==':') {
        c=text[0]&255;
        if(c>='a' && c<='z') c=c-'a'+'A';
        if(c<'A' || c>'P') return 0;
        drive=c-'A'+1;i=2;
    }
    base=ext=dot=0;
    for(;text[i];++i) {
        if(i>=14) return 0;
        c=text[i]&255;
        if(c<33 || c>126 || c==':' || c=='/' || c=='\\' ||
           c=='*' || c=='?' || c==';' || c==',' || c=='=' ||
           c=='<' || c=='>' || c=='|' || c=='"' || c=='[' || c==']')
            return 0;
        if(c>='a' && c<='z') c=c-'a'+'A';
        if(c=='.') {
            if(dot || !base) return 0;
            dot=1;
        } else if(dot) {
            if(ext>=3) return 0;
            raw[9+ext++]=c;
        } else {
            if(base>=8) return 0;
            raw[1+base++]=c;
        }
    }
    if(!base || (dot && !ext)) return 0;
    return drive;
}
int fm_copy_names(list,files,filecount,marks,source,dma,ops)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,source;
char *dma;
struct fm_named_copier *ops;
{
    int chosen[256],n,i,j,k,a,d,c,same,result;
    char target[16],raw[32];
    lastdrive=source;
    if(source<1 || source>16) return -1;
    n=0;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) chosen[n++]=i;
    if(!n && list->navigation.selected) chosen[n++]=list->navigation.selected-1;
    for(i=0;i<n;++i) fm_marks_key(marks,chosen[i]+1,list->navigation.count,44);
    for(i=0;i<n;++i) {
        j=chosen[i];
        for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
        if(k==filecount || files[k].directory) return -1;
        for(;;) {
            target[0]=target[15]=0;
            a=(*ops->ask)(list->names[j],target);
            target[15]=0;
            if(a==-2) return -1;
            if(a<0) return 0;
            if(!a || !target[0]) break;
            d=target_name(target,source,raw);
            if(!d) {
                if(!(*ops->report)("Name is too long, or invalid")) return -1;
                continue;
            }
            same=d==source;
            for(c=1;c<12;++c) {
                a=files[k].raw[c]&127;
                if(a>='a' && a<='z') a=a-'a'+'A';
                if(a!=raw[c]) same=0;
            }
            if(same) {
                if(!(*ops->report)("Source and destination are the same file"))
                    return -1;
                continue;
            }
            lastdrive=d;
            result=(*ops->transfer)(source,files[k].raw,d,raw,dma,ops->cancel);
            if(result!=1) return result;
            fm_marks_key(marks,j+1,list->navigation.count,127);
            break;
        }
    }
    return 1;
}
