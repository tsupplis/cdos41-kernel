/* Local CDOS 4.1 launch bridge; no external utility-library dependency.
 * FMLAUNCH(command,kind,openedFCB): kind 0 native CMD/RSP, kind 1 DOS COM/EXE;
 * 0 success, -1 launch/attach/validation failure. Nonempty command <=127.
 * DOS REQUIRES an exclusive launch context: no other open FCBs/resources
 * affected by BDOS 39, and no preexisting direct children (checked).
 * FMDOSOWN is reset to 0 on entry. After exact OS/context/36-byte FCB-pointer
 * validation it becomes 1: the bridge then consumes ownership on EVERY
 * return, including command/lookup/load failures, by BDOS 39(FFFFh).
 * Caller closes its DOS FCB only if FMDOSOWN returns 0. Never close twice.
 * Native CLI opens/closes its own executable; no native FCB is consumed.
 * Release all FM console locks and restore normal terminal mode beforehand;
 * reopen/repaint FM after return. Native wait is console reattachment, not
 * waitpid: a detached native child may still run. DOS also checks the locked
 * process thread list until direct children terminate. Detached DOS children
 * get their console back via exact-PD 149 while the thread lock protects
 * identity; 149 releases that lock. No detach-to-ancestor gap is allowed.
 * Malformed post-launch thread state waits without output/freeing live memory.
 * Native drive, user, DMA, error mode, multisector count and priority restored.
 * Static buffers: non-reentrant. Exact OS version 1441h is required.
 */
int FMLAUNCH();
int FMDOSOWN();
/* Native BDOS 108 word or DOS selector 0Bh word (AL exit, AH termination).
 * FFFFh if no completed child status was captured. */
int FMEXIT();
/* Native loader/attach CX error, or FFFFh for validation/unsupported ABI. */
int FMLERROR();
/* Read 4 three-byte PCTMP ORDER entries into buffer[1..12], buffer[0]=1.
 * Buffer is 13 bytes, not a NUL-terminated string; 0 success/-1 failure. */
int FMORDER();
/* Default system disk, 1..16; zero if unavailable/unsupported. */
int FMSYSDISK();
