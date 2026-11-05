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

/* Single-drive removable root-directory copy. Caller first confirms
 * "Single drive copy (Y/N)?" and verifies removable drive/root eligibility.
 * fm_copy_swapped(drive,raw,user,dma,cancel,swap): 1 success,0 cancel,-1 error.
 * swap(side), 0 source/1 destination: 1 inserted,0 cancel,-1 UI failure.
 * Caller must request the correct medium; volume identity is operator-owned.
 * All handles close before prompts; 32 full records buffered per exchange.
 * Failed cleanup can retain destination temp/backup (fm_copy_recovery).
 * Source restoration is requested before returning; cancellation of that
 * final request returns error, and caller must not trust/rescan source view.
 */
int fm_copy_swapped();
/* False if the final source insertion was not confirmed. */
int fm_copy_swap_ready();
