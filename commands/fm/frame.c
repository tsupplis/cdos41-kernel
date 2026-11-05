/* Frame glyphs: DATA 09F2/0A0E, descriptors DCE/E60 +21h..27h.
 * Colour translation: DATA 09E2; reverse video: CODE 6B2E..6B51.
 * Rendering affects the border only. The caller owns clearing and content.
 */
#include "layout.h"
#include "frame.h"
static int pc_frame[]={218,191,192,217,196,179};
static int text_frame[]={46,46,124,124,95,124};
static int colours[]={0,1,4,5,2,3,6,7,8,9,12,13,10,11,14,15};
int fm_attribute(foreground,background,reverse)
int foreground,background,reverse;
{
    int fg,bg,t;
    if (foreground<0 || foreground>15 || background<0 || background>15) return -1;
    fg=colours[foreground]; bg=colours[background];
    if (reverse) { t=fg; fg=bg; bg=t; }
    return ((bg<<4)|fg)&127;
}
int fm_frame(canvas,rect,graphics,attribute)
struct fm_canvas *canvas;
struct fm_rect *rect;
int graphics,attribute;
{
    int *g,x,y,right,bottom;
    if (!canvas || !rect || !canvas->cell || rect->width<2 || rect->height<2 ||
        rect->row<0 || rect->column<0 || rect->row>=canvas->rows ||
        rect->column>=canvas->columns || rect->height>canvas->rows-rect->row ||
        rect->width>canvas->columns-rect->column) return 0;
    g=graphics ? pc_frame : text_frame;
    right=rect->column+rect->width-1; bottom=rect->row+rect->height-1;
    if (!(*canvas->cell)(rect->row,rect->column,g[0],attribute) ||
        !(*canvas->cell)(rect->row,right,g[1],attribute) ||
        !(*canvas->cell)(bottom,rect->column,g[2],attribute) ||
        !(*canvas->cell)(bottom,right,g[3],attribute)) return 0;
    for (x=rect->column+1;x<right;++x)
        if (!(*canvas->cell)(rect->row,x,g[4],attribute) ||
            !(*canvas->cell)(bottom,x,g[4],attribute)) return 0;
    for (y=rect->row+1;y<bottom;++y)
        if (!(*canvas->cell)(y,rect->column,g[5],attribute) ||
            !(*canvas->cell)(y,right,g[5],attribute)) return 0;
    return 1;
}
