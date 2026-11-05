/* Internal Type text conversion; no file I/O, prompts or screen locks. */
#ifndef FM_TYPE_H
#define FM_TYPE_H
#define FM_TYPE_MORE 0
#define FM_TYPE_PAGE 1
#define FM_TYPE_END 2
#define FM_TYPE_WIDTH 78
#define FM_TYPE_FIRST_ROW 3

struct fm_type {
    int row, column, limit, status;
};

/* limit is the exclusive bottom row; values <=3 use one content row. */
int fm_type_init();
/* Feed one byte (0..255), or -1 for physical EOF. The callback receives
 * (row,column,character). PAGE consumes its CR; resume before the next byte.
 * Calls while PAGE/END consume nothing and return the existing status.
 * Callback return values are ignored; a null callback is permitted.
 */
int fm_type_feed();
/* After the caller clears the page and restores its header, resume at row 3.
 * Resume has no effect after END or during an unfinished page.
 */
int fm_type_resume();
#endif
