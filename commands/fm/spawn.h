/* CMD/BAT and DOS COM/EXE launch with a bounded command and explicit resolution.
 * 1 means launch succeeded and console returned (not child exit success);
 * 0 means rejected or loader failure. Caller user and DMA are restored.
 * Executable: concrete [D:]8.3, no paths/wildcards; argument tail preserved.
 * DOS requires the exclusive FM bridge: no other open FCBs may exist.
 * Its FMDOSOWN acceptance transfers the resolver FCB on success or failure;
 * before acceptance the resolver retains and closes that FCB.
 */
int fm_spawn();
char *fm_spawn_error();
