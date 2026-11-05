/* FM terminal output, CODE 6CB0/6CC7/6CCD/6CFB.
 * Submit complete sequences to the sink so the native implementation can
 * protect a transaction. Do not mix terminal output with directory actions.
 * Screen dimensions are supplied by terminal discovery, not fixed at 80x24.
 */
#include "screen.h"

int fm_screen_position(screen, row, column)
struct fm_screen *screen;
int row, column;
{
    char sequence[4];
    if (!screen || !screen->write || row < 0 || column < 0 ||
        row >= screen->rows || column >= screen->columns ||
        row > 223 || column > 223) return 0;
    sequence[0] = 27;
    sequence[1] = 'Y';
    sequence[2] = row + 32;
    sequence[3] = column + 32;
    return (*screen->write)(sequence, 4);
}

/* ESC e / ESC f. The original dispatch table supplies these two routines. */
int fm_screen_cursor(screen, visible)
struct fm_screen *screen;
int visible;
{
    char sequence[2];
    if (!screen || !screen->write) return 0;
    sequence[0] = 27;
    sequence[1] = visible ? 'e' : 'f';
    return (*screen->write)(sequence, 2);
}
