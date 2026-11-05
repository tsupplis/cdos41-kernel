/* Original Print byte conversion, without device or file I/O. */
#ifndef FM_PRTEXT_H
#define FM_PRTEXT_H
#define FM_PRTEXT_MORE 0
#define FM_PRTEXT_END 1
#define FM_PRTEXT_ERROR (-1)

struct fm_prtext {
    int column, status;
};

int fm_prtext_init();
/* Feed 0..255 or -1 for EOF. put(ch) must return nonzero on success.
 * column is modulo eight; END and ERROR persist until init.
 * A null callback is an error when output is needed. The caller emits
 * the final form feed and polls for cancellation between source bytes.
 */
int fm_prtext_feed();
#endif
