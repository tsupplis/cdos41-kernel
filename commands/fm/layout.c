/* All five menu positions, CODE 8032h..8565h.
 * expanded_bottom is the original DATA 0D00h flag, relevant to position 2.
 * Invalid geometry is rejected without modifying the caller's layout.
 */
#include "fm.h"
#include "layout.h"
int fm_layout_calculate(out, config, rows, columns, expanded_bottom)
struct fm_layout *out;
struct fm_config *config;
int rows, columns, expanded_bottom;
{
    struct fm_layout result;
    int position, menu, prompt, top, bottom, left, right, width, height;
    if (!out || !config) return 0;
    position=config->value[1]&255;
    if (position<1 || position>5) return 0;
    prompt=config->value[9]&255;
    top=config->value[10]&255; bottom=config->value[11]&255;
    left=config->value[12]&255; right=config->value[13]&255;
    width=columns-left-right; height=rows-top-bottom-prompt;
    if (rows<1 || rows>223 || columns<1 || columns>223 ||
        width<3 || height<3 || prompt<1) return 0;
    result.files.row=top; result.files.column=left;
    result.files.width=width; result.files.height=height;
    result.menu.row=result.files.row;
    result.menu.column=result.files.column;
    result.menu.width=result.files.width;
    result.menu.height=result.files.height;
    result.prompt.row=top+height; result.prompt.column=left;
    result.prompt.width=width; result.prompt.height=prompt;
    if (position==1 || position==3) {
        menu=(config->value[8]&255)+3;
        if (width-menu<3) return 0;
        result.menu.width=menu;
        result.files.width=width-menu;
        if (position==1) result.menu.column=left+width-menu;
        else result.files.column=left+menu;
    } else {
        menu=3;
        if (position==2 && expanded_bottom) menu=8;
        if (position==5) menu=1;
        if (height-menu<3) return 0;
        result.menu.height=menu;
        result.files.height=height-menu;
        if (position==4) result.files.row=top+menu;
        else result.menu.row=top+height-menu;
    }
    out->files.row=result.files.row;
    out->files.column=result.files.column;
    out->files.width=result.files.width;
    out->files.height=result.files.height;
    out->menu.row=result.menu.row;
    out->menu.column=result.menu.column;
    out->menu.width=result.menu.width;
    out->menu.height=result.menu.height;
    out->prompt.row=result.prompt.row;
    out->prompt.column=result.prompt.column;
    out->prompt.width=result.prompt.width;
    out->prompt.height=result.prompt.height;
    return 1;
}

/* Retained for callers explicitly requesting the right-hand menu. */
int fm_layout_right(out, config, rows, columns)
struct fm_layout *out;
struct fm_config *config;
int rows, columns;
{
    if (!config || (config->value[1]&255)!=1) return 0;
    return fm_layout_calculate(out,config,rows,columns,0);
}
