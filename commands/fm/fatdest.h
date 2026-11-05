/* FAT directory alias adapter. Caller supplies a directory entry and its
 * current DMA. Returns a process-local alias (14..16), 0 on failure, or -1
 * when destination resolves to the source directory. Never borrows an
 * inherited mapping; mappings created here live until process termination.
 * FMLOC(drive, int out[4]) returns physical drive (1..13), media sequence,
 * directory cluster, mapped flag. An unassigned alias is physical=0,mapped=0
 * with return 1; return 0 means inspection failure, not a free alias.
 */
int fm_fat_destination();
char *fm_fat_destination_error();

/* Bookmarks pin module-owned aliases. Capture accepts the source location;
 * pin the new capture before unpinning the old one when replacing a mark.
 * Capture/clone return alias14..16 or0. Pinned aliases are never reused.
 * valid/pin/unpin return1 or0; unpin only changes local bookkeeping.
 * same returns1 for equal physical drive+cluster, 0 otherwise or on error;
 * callers must validate the bookmark before treating 0 as different.
 * Identity checks inspect current kernel mappings only: media replacement
 * is detected after the kernel updates its media sequence/mapping, not by
 * independently probing or logging the disk.
 */
int fm_fat_capture();
int fm_fat_pin();
int fm_fat_unpin();
int fm_fat_valid();
int fm_fat_same();
int fm_fat_clone();
/* Immediately after intentional directory navigation, refresh an already
 * owned, unpinned working alias. Never adopts inherited or pinned aliases.
 * Returns1 on success,0 on failure; call before valid() on the changed alias.
 */
int fm_fat_refresh_owned();

/* Resolve the source's physical full path and return a scratch root alias.
 * fm_fat_root(source,path,capacity,dma): 14..16 on success, 0 on failure.
 * At most66 path characters plus NUL. Source and pins never move; consumes
 * search state, restores caller user/DMA. Requires a spare owned/free alias
 * and stable mounted media. Caller may use the returned root for file I/O.
 */
int fm_fat_root();

/* Same operation, also excludes protect from scratch-alias allocation. */
int fm_fat_root_protected();
