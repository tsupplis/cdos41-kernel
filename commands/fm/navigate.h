#ifndef FM_NAVIGATE_H
#define FM_NAVIGATE_H
/* Original selection is one-based; offset counts entries before the page. */
struct fm_navigation { int count, selected, offset, capacity, columns; };
int fm_navigate();
#endif
