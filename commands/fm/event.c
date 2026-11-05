/* Connect input, navigation and rendering without disk-changing actions.
 * Screen ownership lasts only for repaint, never for an input wait.
 */
#include "event.h"
int fm_browser_paint(view, canvas, console)
struct fm_browser *view;
struct fm_canvas *canvas;
struct fm_console *console;
{
    int result, locking;
    if (!view || !canvas || !console) return 0;
    locking=console->acquire!=0 || console->release!=0;
    if (locking && !fm_console_begin(console)) return 0;
    result=fm_browser_draw(view,canvas);
    if (!fm_console_end(console)) return 0;
    return result;
}
int fm_browser_step(view, canvas, console, source, target, length)
struct fm_browser *view;
struct fm_canvas *canvas;
struct fm_console *console;
char *source, *target;
int length;
{
    int key, moved;
    if (!view || !canvas || !console) return -1;
    key=fm_console_key(console,source,target,length);
    if (key==-1) return 0;
    if (key<0) return -1;
    if (key==27) return 2;
    moved=fm_browser_key(view,key);
    if (moved<0) return -1;
    if (!moved) return 0;
    return fm_browser_paint(view,canvas,console) ? 1 : -1;
}
