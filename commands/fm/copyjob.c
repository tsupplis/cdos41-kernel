/* Ordinary drive-copy batch, CODE 4766: stop on first error/cancellation,
 * retaining failed and unprocessed selections. Source entries never change.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "copyjob.h"
int fm_copy_batch(list,files,filecount,marks,source,destination,dma,ops)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,source,destination;
char *dma;
struct fm_copier *ops;
{
    int chosen[256],n,i,j,k,result;
    n=0;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) chosen[n++]=i;
    if(!n && list->navigation.selected) chosen[n++]=list->navigation.selected-1;
    for(i=0;i<n;++i) fm_marks_key(marks,chosen[i]+1,list->navigation.count,44);
    for(i=0;i<n;++i) {
        j=chosen[i];
        for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
        if(k==filecount || files[k].directory) return -1;
        if(!(*ops->notice)(list->names[j])) return -1;
        result=(*ops->transfer)(source,files[k].raw,destination,dma,ops->cancel);
        if(result!=1) return result;
        fm_marks_key(marks,j+1,list->navigation.count,127);
    }
    return 1;
}

/* Ordinary drive copy refuses the same drive before changing selections. */
int fm_copy_files(list,files,filecount,marks,source,destination,dma,ops)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,source,destination;
char *dma;
struct fm_copier *ops;
{
    if(source==destination) return -1;
    return fm_copy_batch(list,files,filecount,marks,source,destination,dma,ops);
}
