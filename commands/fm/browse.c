/* Compose the tested name, key, navigation and cell-rendering cores.
 * This is a read-only file pane, not the original application's full UI.
 * Names remain owned by the caller and must have twelve display bytes.
 */
#include "browse.h"
#include "dirlist.h"
#include "keys.h"

int fm_browser_open(view, names, count, area, stride, normal, selected)
struct fm_browser *view;
char **names;
int count, stride, normal, selected;
struct fm_rect *area;
{
    int columns, rows, i;
    if (!view || !area || count < 0 || count > 32000 ||
        (count && !names) || stride < FM_NAME_WIDTH || stride > 255 ||
        area->row < 0 || area->column < 0 || area->width < stride+2 ||
        area->height < 3 || area->width > 255 || area->height > 255) return 0;
    columns = (area->width-2)/stride;
    rows = area->height-2;
    if (columns > 127 || columns*rows > 255) return 0;
    for (i=0; i<count; ++i) if (!names[i]) return 0;
    view->area.row=area->row; view->area.column=area->column;
    view->area.width=area->width; view->area.height=area->height;
    view->navigation.count=count;
    view->navigation.selected=count ? 1 : 0;
    view->navigation.offset=0;
    view->navigation.columns=columns;
    view->navigation.capacity=columns*rows;
    view->names=names; view->stride=stride;
    view->normal=normal; view->selected=selected;
    return 1;
}

int fm_browser_key(view, key)
struct fm_browser *view;
int key;
{
    if (!view) return -1;
    return fm_navigate(&view->navigation, fm_key_normalize(key));
}

int fm_browser_draw(view, canvas)
struct fm_browser *view;
struct fm_canvas *canvas;
{
    int row, column, i, j, index, attr;
    if (!view || !canvas || !canvas->cell || view->area.row<0 ||
        view->area.column<0 || view->area.row>canvas->rows-view->area.height ||
        view->area.column>canvas->columns-view->area.width) return 0;
    /* Clear the whole interior, including the last page's unused cells. */
    for (row=1; row<view->area.height-1; ++row)
        for (column=1; column<view->area.width-1; ++column)
            if (!(*canvas->cell)(view->area.row+row,view->area.column+column,
                                ' ',view->normal)) return 0;
    if (!fm_frame(canvas,&view->area,1,view->normal)) return 0;
    for (i=0; i<view->navigation.capacity; ++i) {
        index=view->navigation.offset+i;
        if (index>=view->navigation.count) break;
        row=view->area.row+1+i/view->navigation.columns;
        column=view->area.column+1+(i%view->navigation.columns)*view->stride;
        attr=index+1==view->navigation.selected ? view->selected : view->normal;
        for (j=0; j<FM_NAME_WIDTH; ++j)
            if (!(*canvas->cell)(row,column+j,view->names[index][j]&127,attr))
                return 0;
    }
    return 1;
}
