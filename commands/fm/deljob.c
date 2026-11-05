/* Original CODE 4FFE/5165. One confirmation covers the selected files.
 * Failed entries retain their marks; successful entries are removed by
 * the caller's rescan. The native adapter never clears file attributes.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "deljob.h"
int fm_delete_files(list,files,filecount,marks,drive,ops)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,drive;
struct fm_eraser *ops;
{
    int chosen[256],n,i,j,k,result;
    n=0;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) chosen[n++]=i;
    if(!n && list->navigation.selected) chosen[n++]=list->navigation.selected-1;
    if(!n) return 2;
    result=(*ops->confirm)();
    if(result<0) return 0;
    if(!result) return 2;
    for(i=0;i<n;++i) {
        j=chosen[i];
        for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
        if(k<filecount && !files[k].directory &&
           (*ops->erase)(drive,files[k].raw))
            fm_marks_key(marks,j+1,list->navigation.count,127);
        else fm_marks_key(marks,j+1,list->navigation.count,44);
    }
    return 1;
}
