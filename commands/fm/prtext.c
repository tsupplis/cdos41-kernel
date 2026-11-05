/* Original Print CODE 3E1Ah, conversion at 3EDFh..3F9Ch. */
#include "prtext.h"

int fm_prtext_init(text)
struct fm_prtext *text;
{
    text->column = 0;
    text->status = FM_PRTEXT_MORE;
    return text->status;
}

int fm_prtext_feed(text, ch, put)
struct fm_prtext *text;
int ch;
int (*put)();
{
    int count;

    if (text->status != FM_PRTEXT_MORE) return text->status;
    /* The original compares AL with FF before stripping the high bit. */
    if (ch == -1 || ch == 255 || (ch & 127) == 26) {
        text->status = FM_PRTEXT_END;
        return text->status;
    }
    ch &= 127;
    count = 1;
    if (ch == 9) {
        count = 8 - text->column;
        ch = ' ';
    } else if (ch < 32 && ch != 10 && ch != 12 && ch != 13)
        ch = ' ';
    while (count--) {
        if (!put || !(*put)(ch)) {
            text->status = FM_PRTEXT_ERROR;
            return text->status;
        }
        if (ch == 13) text->column = 0;
        else if (ch != 10 && ch != 12)
            text->column = (text->column + 1) & 7;
    }
    return text->status;
}
