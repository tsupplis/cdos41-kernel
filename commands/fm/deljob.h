/* confirm: 1 yes, 0 cancel, -1 display/input failure. erase: 1 success. */
struct fm_eraser { int (*confirm)(); int (*erase)(); };
/* 2 cancelled/no selection, 1 processed, 0 display/input failure. */
int fm_delete_files();
