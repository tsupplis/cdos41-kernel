/* Read-only menu focus; action numbers refer to menu.c, never execute here. */
#include "navigate.h"
struct fm_focus {
    struct fm_navigation navigation;
    int active, setup, file_selection;
};
int fm_focus_open();
int fm_focus_key();
int fm_focus_index();
