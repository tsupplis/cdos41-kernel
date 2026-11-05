/* One transfer: 1 success, 0 cancelled, -1 error. notice returns boolean.
 * The transfer adapter owns I/O cleanup; no screen lock spans a transfer. */
struct fm_copier { int (*transfer)(); int (*cancel)(); int (*notice)(); };
int fm_copy_files();

/* Location-aware adapters perform their own same-location check. */
int fm_copy_batch();
