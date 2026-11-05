/* File and setup menu metadata; independent of renderer and file operations. */
struct fm_menu_item {
    char *action;
    char *label;
    char *description;
    char *command;
    int minimum;
    int maximum;
};
extern struct fm_menu_item fm_menu_items[];
extern int fm_menu_count;
extern int fm_file_menu_count;
