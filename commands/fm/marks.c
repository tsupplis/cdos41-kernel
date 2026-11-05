/* CODE 9029h adds a mark for comma/Insert without moving selection.
 * CODE 9214h removes it for Delete when no filename search is active.
 * Repeated add/remove is idempotent; count cannot underflow or duplicate.
 */
#include "marks.h"
#include "browse.h"
int fm_marks_clear(marks)
struct fm_marks *marks;
{
    int i;
    for(i=0;i<256;++i) marks->value[i]=0;
    marks->count=0;return 1;
}
int fm_marks_key(marks,selected,total,key)
struct fm_marks *marks;
int selected,total,key;
{
    int value;
    if(key!=44 && key!=127) return -1;
    if(!marks || total<0 || total>256 || selected<1 || selected>total) return 0;
    value=key==44;
    if(marks->value[selected-1]==value) return 0;
    marks->value[selected-1]=value;marks->count+=value ? 1 : -1;
    return 1;
}
/* Overlay marked names after the file pane, while the caller owns its lock.
 * The active cursor and marked names both use reverse-video highlighting.
 */
int fm_marks_draw(marks,view,canvas)
struct fm_marks *marks;
struct fm_browser *view;
struct fm_canvas *canvas;
{
    int i,j,index,row,column;
    if(!marks || !view || !canvas || !canvas->cell || view->navigation.count>256) return 0;
    for(i=0;i<view->navigation.capacity;++i) {
        index=view->navigation.offset+i;
        if(index>=view->navigation.count) break;
        if(!marks->value[index]) continue;
        row=view->area.row+1+i/view->navigation.columns;
        column=view->area.column+1+i%view->navigation.columns*view->stride;
        for(j=0;j<12;++j)
            if(!(*canvas->cell)(row,column+j,view->names[index][j]&127,view->selected)) return 0;
    }
    return 1;
}
