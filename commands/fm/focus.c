/* Tab normalizes to 3 in CODE 68C8h and changes pane in the main loop
 * at CODE 0906h/0AE7h. Escape backs out of the menu. F10 is a command
 * prompt request in the original, NOT the menu-focus key.
 * This controller exposes menu selection without enabling file operations.
 */
#include "focus.h"
#include "menu.h"
#include "keys.h"
static int group(focus,setup,selection)
struct fm_focus *focus;
int setup,selection;
{
    focus->setup=setup;
    focus->navigation.count=setup ? fm_menu_count-fm_file_menu_count : fm_file_menu_count;
    focus->navigation.selected=selection;
    focus->navigation.offset=selection>focus->navigation.capacity ?
        selection-focus->navigation.capacity : 0;
    return 1;
}
int fm_focus_open(focus,rows)
struct fm_focus *focus;
int rows;
{
    if(!focus || rows<1 || rows>255) return 0;
    focus->active=0;focus->file_selection=1;
    focus->navigation.capacity=rows;focus->navigation.columns=1;
    return group(focus,0,1);
}
int fm_focus_index(focus)
struct fm_focus *focus;
{
    return (focus->setup ? fm_file_menu_count : 0)+focus->navigation.selected-1;
}
/* -1: key belongs to files; 0: consumed; 1: repaint; 2: selected action.
 * Enter on Set Up System opens its menu; Escape returns to the file menu,
 * then the file pane. No external program is launched here.
 */
int fm_focus_key(focus,key)
struct fm_focus *focus;
int key;
{
    int moved;
    key=fm_key_normalize(key);
    if(key==3) {focus->active=!focus->active;return 1;}
    if(!focus->active) return -1;
    if(key==27) {
        if(focus->setup) group(focus,0,focus->file_selection);
        else focus->active=0;
        return 1;
    }
    if(key==13) {
        if(!focus->setup && fm_focus_index(focus)==16) {
            focus->file_selection=focus->navigation.selected;
            group(focus,1,1);return 1;
        }
        return 2;
    }
    moved=fm_navigate(&focus->navigation,key);
    return moved>0 ? 1 : 0;
}
