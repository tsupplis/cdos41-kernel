/* Read-only browser composition. Geometry is supplied by the layout caller;
 * column spacing is explicit until all original grid modes are recovered.
 */
#include "frame.h"
#include "layout.h"
#include "navigate.h"
struct fm_browser {
    struct fm_navigation navigation;
    struct fm_rect area;
    char **names;
    int stride, normal, selected;
};
int fm_browser_open();
int fm_browser_key();
int fm_browser_draw();
