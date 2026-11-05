/* Read-only browser event pump. Caller handles scheduling when idle.
 * Return values: -1 error, 0 idle/unhandled key, 1 repainted, 2 Escape.
 */
#include "browse.h"
#include "conio.h"
int fm_browser_paint();
int fm_browser_step();
