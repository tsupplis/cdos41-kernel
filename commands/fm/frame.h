/* Cell sink is supplied by the native or host backend. */
struct fm_canvas { int rows, columns; int (*cell)(); };
int fm_frame();
int fm_attribute();
