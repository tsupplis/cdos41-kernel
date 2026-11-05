/* Uses struct fm_runner from runjob.h (invoke/report callbacks).
 * Global menu indices match menu.c. Returns 1 success,0 rejection/launch
 * failure,-1 report/UI failure. Success clears marks except Help, whose
 * original handler preserves selection. All failures retain marks.
 * Only minimum>0 operations use and mark the current cursor as a fallback.
 */
int fm_external();
int fm_external_available();
/* fm_external_boot(list,files,filecount,marks,ask,ops).
 * ask(buffer[6]): 1 entered text, 0 cancel, -1 UI error. Caller prompts
 * "Hard disk partition type? (DOS or CP/M)" with a five-character limit.
 * Exact case-insensitive DOS or CP/M accepted; invalid text retries and
 * empty text cancels. Generic fm_external(25) remains unavailable.
 * Function/Serial known chains always run both steps as original RUNMENU;
 * either invocation failing retains selection, both succeeding clears it.
 */
int fm_external_boot();
