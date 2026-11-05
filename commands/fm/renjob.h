/* ask(old,text): 1 supplied, 0 skip, -1 cancel batch, -2 display failure.
 * change follows renio.h; report(message) is display only. */
struct fm_renamer { int (*ask)(); int (*change)(); int (*report)(); };
int fm_rename_files();
