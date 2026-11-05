/* Copy a concrete directory-entry filename between explicit drives in the
 * current user area. 1 success, 0 cancelled, -1 error. cancel may be zero.
 * Full 128-byte records; no source attributes are propagated. Caller DMA is
 * restored. A nonempty recovery basename must be retained for manual recovery.
 */
int fm_copy_file();
char *fm_copy_recovery();
/* Clear a previous recovery notice before a new batch, even if it fails
 * validation before calling the transfer engine. Does not touch disk. */
int fm_copy_reset();
/* Explicit destination name, in directory-entry format. Allows same-drive
 * copies only when the normalized source and destination names differ.
 * Both input entries are unchanged; status/recovery rules match copy_file.
 */
int fm_copy_named();
/* Explicit user-area variant (0..15). Restores entry user and DMA even
 * after cancellation/error; same drive/name requires different users.
 * Caller must restrict different users on one drive to CP/M media.
 */
int fm_copy_users();
