/* Original Print action CODE 3E1A/4017: ordered selections, per-character
 * cancellation and one trailing form feed per opened file. Disk reads are
 * shared with Type. Failed or unfinished files remain marked.
 */
#include "browse.h"
#include "scan.h"
#include "marks.h"
#include "typeio.h"
#include "prtext.h"
#include "printjob.h"
static char record[128];
/* Return 1 complete or cancelled, 0 unavailable printer, -1 I/O failure. */
int fm_print_files(list,files,filecount,marks,drive,dma,printer)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,drive;
char *dma;
struct fm_printer *printer;
{
    struct fm_prtext state;
    int chosen[256],n,i,j,k,r,status,stop,errors,complete;
    n=0;stop=0;errors=0;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) chosen[n++]=i;
    if(!n && list->navigation.selected) chosen[n++]=list->navigation.selected-1;
    if(!n) return 1;
    for(i=0;i<n;++i) fm_marks_key(marks,chosen[i]+1,list->navigation.count,44);
    if(!(*printer->attach)()) return 0;
    for(i=0;i<n && !stop;++i) {
        j=chosen[i];
        for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
        if(k==filecount || !fm_type_open(drive,files[k].raw,dma)) {
            errors=1;continue;
        }
        complete=0;status=FM_PRTEXT_MORE;fm_prtext_init(&state);
        if(!(*printer->notice)(list->names[j])) {errors=1;stop=1;}
        while(!stop && status!=FM_PRTEXT_END) {
            r=fm_type_read(record);
            if(r<0) {errors=1;break;}
            if(!r) {complete=1;break;}
            for(k=0;k<128 && !stop && status!=FM_PRTEXT_END;++k) {
                status=fm_prtext_feed(&state,record[k]&255,printer->put);
                if(status==FM_PRTEXT_END) complete=1;
                else if(status==FM_PRTEXT_ERROR) {errors=1;stop=1;}
                else {
                    r=(*printer->key)();
                    if(r) stop=1;
                    if(r<0) errors=1;
                }
            }
        }
        if(!fm_type_close()) {errors=1;complete=0;}
        if(!(*printer->put)(12)) {errors=1;stop=1;complete=0;}
        if(complete && !stop) fm_marks_key(marks,j+1,list->navigation.count,127);
    }
    if(!(*printer->detach)()) errors=1;
    return errors ? -1 : 1;
}
