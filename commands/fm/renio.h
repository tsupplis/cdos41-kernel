/* Concrete bare-name rename. raw/newraw are 32-byte directory entries.
 * 1 success, 0 invalid input, -2 destination exists, -1 other BDOS error.
 * Inputs and newraw remain unchanged on failure. DMA is never changed.
 */
int fm_rename_file();

int fm_set_attributes();
