/* Rename selection loop from CODE 4E24/4FD3. No deletion or overwrite.
 * Names are changed in-place only after BDOS success. Caller then resorts
 * and remaps retained marks; indices stay stable throughout this loop.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "renjob.h"
int fm_rename_files(list,files,filecount,marks,drive,dma,ops)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,drive;
char *dma;
struct fm_renamer *ops;
{
    int chosen[256],n,i,j,k,a,r,c;
    char target[13],newraw[32];
    n=0;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) chosen[n++]=i;
    if(!n && list->navigation.selected) chosen[n++]=list->navigation.selected-1;
    for(i=0;i<n;++i) fm_marks_key(marks,chosen[i]+1,list->navigation.count,44);
    for(i=0;i<n;++i) {
        j=chosen[i];
        for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
        if(k==filecount) continue;
        do {
            target[0]=0;
            a=(*ops->ask)(list->names[j],target);
            if(a==-2) return 0;
            if(a<0) return 1;
            if(!a || !target[0]) break;
            if(target[1]==':') {
                if(!(*ops->report)("You cannot specify a drive.")) return 0;
                r=0;
            } else {
                r=(*ops->change)(drive,files[k].raw,target,dma,newraw);
                if(!r && !(*ops->report)("Name is too long, or invalid")) return 0;
            }
        } while(!r);
        if(!a || !target[0]) continue;
        if(r==1) {
            for(c=0;c<32;++c) files[k].raw[c]=newraw[c];
            fm_directory_name(files[k].raw,files[k].name,FM_NAME_SIZE);
            fm_marks_key(marks,j+1,list->navigation.count,127);
        } else if(!(*ops->report)(r==-2 ? "File already EXISTS, not renamed" :
                                            "File not renamed")) return 0;
    }
    return 1;
}
