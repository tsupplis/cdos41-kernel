/* Original viewer CODE 3AB8h: fixed-width, CR-driven, seven-bit text. */
#include "type.h"

int fm_type_init(view, limit)
struct fm_type *view;
int limit;
{
    view->row = FM_TYPE_FIRST_ROW;
    view->column = 0;
    view->limit = limit > FM_TYPE_FIRST_ROW ? limit : FM_TYPE_FIRST_ROW+1;
    view->status = FM_TYPE_MORE;
    return view->status;
}

int fm_type_feed(view, ch, cell)
struct fm_type *view;
int ch;
int (*cell)();
{
    if (view->status != FM_TYPE_MORE) return view->status;
    if (ch == -1) {
        view->status = FM_TYPE_END;
        return view->status;
    }
    ch &= 127;
    if (ch == 26) view->status = FM_TYPE_END;
    else if (ch == 13) {
        view->column = 0;
        ++view->row;
        if (view->row >= view->limit) view->status = FM_TYPE_PAGE;
    } else if (ch == 9) {
        do {
            if (view->column >= FM_TYPE_WIDTH) break;
            if (cell) (*cell)(view->row, view->column, ' ');
            ++view->column;
        } while (view->column % 8);
    } else if (ch != 10 && view->column < FM_TYPE_WIDTH) {
        if (ch < 32) ch = ' ';
        if (cell) (*cell)(view->row, view->column, ch);
        ++view->column;
    }
    return view->status;
}

int fm_type_resume(view)
struct fm_type *view;
{
    if (view->status == FM_TYPE_PAGE) {
        view->row = FM_TYPE_FIRST_ROW;
        view->column = 0;
        view->status = FM_TYPE_MORE;
    }
    return view->status;
}
