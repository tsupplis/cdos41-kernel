/* Logical rectangles; excludes borders from interior geometry. */
struct fm_rect { int row, column, width, height; };
struct fm_layout { struct fm_rect files, menu, prompt; };
int fm_layout_right();
int fm_layout_calculate();
