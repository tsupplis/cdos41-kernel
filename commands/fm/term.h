/* CDOS PC-window backend. A successful open installs canvas and console
 * callbacks; close releases ownership. No pointers are exposed to UI code.
 */
int fm_term_open();
int fm_term_close();
