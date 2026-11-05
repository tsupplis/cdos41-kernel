/* Terminal protocol only. The native sink owns console locking and BDOS I/O. */
struct fm_screen {
    int rows, columns;
    int (*write)();
};
int fm_screen_position();
int fm_screen_cursor();
