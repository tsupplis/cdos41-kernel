/* Pure original Backup control-file formatter; no BDOS or mark mutation.
 * fm_backup_control(list,files,filecount,marks,source,user,fat,path,
 *                   destination,whole,put)
 * source is 1..16, user 0..15, destination 1..2, fat/whole are booleans.
 * FAT requires a nonempty path (maximum 127 printable characters).
 * whole=0 requires marks; whole=1 emits a wildcard and ignores marks.
 * put(byte) returns 1 on success; any other result stops emission.
 * Returns 1 complete, 0 invalid input/selection or writer failure.
 * Validation precedes emission. Output is CRLF text without record padding.
 * Callers own buffering, close/commit, location restoration and child launch.
 */
int fm_backup_control();
char *fm_backup_error();

/* Run exact BACK/REST workflow. 1 launched,0 refused/loader failure,
 * -1 I/O error,-2 location restoration failed: caller must exit safely. */
int fm_backup_run();
char *fm_backup_io_error();
/* -1 unavailable/invalid, 0 removable, 1 permanent. */
int fm_native_permanent();
