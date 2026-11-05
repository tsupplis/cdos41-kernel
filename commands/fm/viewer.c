/* Internal paged Type action, from CODE 3AB8/3E02.
 * Files are never changed. Completed selections are unmarked; open/read
 * failures and cancelled files remain marked. Disk/input calls occur only
 * after releasing the direct-screen lock.
 */
#include "event.h"
#include "scan.h"
#include "marks.h"
#include "type.h"
#include "typeio.h"
#include "viewer.h"
static struct fm_canvas *out;
static struct fm_console *terminal;
static int colour, render_error;
static char record[128];
static int vcell(row,col,ch)
int row,col,ch;
{
    int ok;
    ok=(*out->cell)(row,col,ch,colour);
    if(!ok) render_error=1;
    return ok;
}
static int line(row,prefix,name)
int row;
char *prefix,*name;
{
    int i,ch;
    for(i=0;i<80;++i) {
        if(*prefix) ch=*prefix++;
        else if(name && *name) ch=*name++;
        else ch=' ';
        if(!vcell(row,i,ch)) return 0;
    }
    return 1;
}
static int page(name)
char *name;
{
    int row,ok;
    if(!fm_console_begin(terminal)) return 0;
    ok=1;
    for(row=0;row<24 && ok;++row) ok=line(row,"",0);
    if(ok) ok=line(0,"Typing ",name);
    if(!fm_console_end(terminal)) ok=0;
    return ok;
}
static int prompt(message,name)
char *message,*name;
{
    int ok;
    if(!fm_console_begin(terminal)) return 0;
    ok=line(23,message,name);
    if(!fm_console_end(terminal)) ok=0;
    return ok;
}
static int waitkey()
{
    int key;
    do {
        key=fm_console_key(terminal,0,0,0);
        if(key==-1) __BDOS(142,0);
    } while(key==-1);
    return key;
}
/* Return 1 normal/cancel, 0 display/input failure, -1 file I/O failure. */
int fm_view_files(list,files,filecount,marks,drive,dma,canvas,console,attr)
struct fm_browser *list;
struct fm_file *files;
struct fm_marks *marks;
int filecount,drive,attr;
char *dma;
struct fm_canvas *canvas;
struct fm_console *console;
{
    struct fm_type state;
    int chosen[256],n,i,j,k,status,readresult,key,ok,errors,stopped;
    out=canvas;terminal=console;colour=attr;n=0;errors=0;stopped=0;render_error=0;
    for(i=0;i<list->navigation.count;++i)
        if(marks->value[i]) chosen[n++]=i;
    if(!n && list->navigation.selected) chosen[n++]=list->navigation.selected-1;
    for(i=0;i<n && !stopped;++i) {
        j=chosen[i];
        for(k=0;k<filecount;++k) if(list->names[j]==files[k].name) break;
        if(k==filecount || !fm_type_open(drive,files[k].raw,dma)) {
            fm_marks_key(marks,j+1,list->navigation.count,44);errors=1;continue;
        }
        fm_type_init(&state,23);ok=page(list->names[j]);status=FM_TYPE_MORE;
        while(ok && status!=FM_TYPE_END && !stopped) {
            readresult=fm_type_read(record);
            if(readresult<0) {errors=1;break;}
            if(!readresult) {status=FM_TYPE_END;break;}
            if(!fm_console_begin(terminal)) {ok=0;break;}
            for(k=0;k<128 && ok && !stopped && status!=FM_TYPE_END;++k) {
                status=fm_type_feed(&state,record[k]&255,vcell);
                if(render_error) {ok=0;break;}
                if(status==FM_TYPE_PAGE) {
                    if(!fm_console_end(terminal)) {ok=0;break;}
                    ok=prompt("Press return for next page",0);
                    key=ok ? waitkey() : -2;
                    if(key<0) ok=0;
                    if(key!=13) stopped=1;
                    else if(ok) {
                        ok=page(list->names[j]);fm_type_resume(&state);status=FM_TYPE_MORE;
                        if(ok) ok=fm_console_begin(terminal);
                    }
                }
            }
            if(!fm_console_end(terminal)) ok=0;
        }
        if(!fm_type_close()) {errors=1;status=FM_TYPE_MORE;}
        if(!ok) return 0;
        if(status!=FM_TYPE_END || stopped) fm_marks_key(marks,j+1,list->navigation.count,44);
        else fm_marks_key(marks,j+1,list->navigation.count,127);
        if(stopped) break;
        if(status==FM_TYPE_END) {
            if(!fm_console_begin(terminal)) return 0;
            ok=line(0,"Last page of ",list->names[j]);
            if(!fm_console_end(terminal) || !ok) return 0;
            if(!prompt(i+1<n ? "Press return to type " : "Press any key to quit",
                       i+1<n ? list->names[chosen[i+1]] : 0)) return 0;
            key=waitkey();if(key<0) return 0;
            if(i+1<n && key!=13) stopped=1;
        }
    }
    return errors ? -1 : 1;
}
