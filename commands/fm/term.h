/* CDOS PC-window or TERM.DAT serial backend. A successful open installs canvas and console
 * callbacks; close releases ownership. No pointers are exposed to UI code.
 */
int fm_term_open();
int fm_term_close();

int fm_term_cursor();
