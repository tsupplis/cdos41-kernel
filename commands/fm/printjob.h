/* Printer callbacks run outside display ownership. key: 0 idle, 1 cancel,
 * -1 input error. Other callbacks return 1 success, 0 failure. */
struct fm_printer {
    int (*attach)();
    int (*detach)();
    int (*put)();
    int (*key)();
    int (*notice)();
};
int fm_print_files();
int fm_printer_native();
