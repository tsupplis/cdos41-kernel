# CALLCOMPAT — CDOS 4.1 commands

2026-11-05. Source/API review of all 69 executable artifacts in the distribution
recipe. This is not a cross-version runtime certification.

**3.1 / 4.1**: native baseline. **Degraded**: works without enhanced behaviour.
**Specific**: no reliable working fallback without our extension.
DOS markers give the DOS API level; an additional unmet native requirement is
noted where applicable. Preserved distribution binaries are classified as 4.1.

**Adaptive**: deliberately detects the OS version or available services and selects
a supported path; unavailable optional features do not prevent normal use.

| Command | Status | Comment |
| --- | --- | --- |
| ASM80.CMD <!-- commands/asm80/asm80.cmd --> | 3.1 |  |
| ASM86.CMD <!-- commands/asm86/asm86.cmd --> | Adaptive | 3.1 baseline. Version-gated BDOS 108 exit-status reporting; normal operation does not require it. |
| BATCH.CMD <!-- commands/batch/batch.cmd --> | Specific | Specific CDOS 4.1 PCTMP environment API (0Ah). No safe pre-call capability guard; behaviour on the vanilla dispatcher is unpredictable. |
| CHDIR.CMD <!-- commands/chdir/chdir.cmd --> | 4.1 |  |
| CHKCPMFS.CMD <!-- commands/chkcpmfs/chkcpmfs.cmd --> | 3.1 |  |
| CHKDOSFS.CMD <!-- commands/chkdosfs/chkdosfs.cmd --> | 4.1 |  |
| CHSET.CMD <!-- commands/chset/chset.cmd --> | Degraded | 3.1 baseline. Without loader support for TAIL=KEEP, that setting does not preserve command-tail case; other settings still work. |
| COPY.EXE <!-- commands/copy/copy.exe --> | DOS 1.0 + native BDOS | Also requires native Concurrent BDOS calls: will not work under plain DOS 1.0/2.0. |
| COPYMENU.CMD <!-- commands/copymenu/copymenu.cmd --> | 4.1 |  |
| DATE.CMD <!-- commands/date/date.cmd --> | 3.1 |  |
| DATE.EXE <!-- commands/datetime/date.exe --> | DOS 1.0 + native BDOS | Also requires native Concurrent BDOS calls: will not work under plain DOS 1.0/2.0. |
| TIME.EXE <!-- commands/datetime/time.exe --> | DOS 1.0 + native BDOS | Also requires native Concurrent BDOS calls: will not work under plain DOS 1.0/2.0. |
| DDT86.CMD <!-- commands/ddt86/ddt86.cmd --> | 3.1 |  |
| DFORM.CMD <!-- commands/dform/dform.cmd --> | Specific | Specific CDOS 4.1 only. |
| DIR.CMD <!-- commands/dir/dir.cmd --> | 3.1 |  |
| DCOMP.CMD <!-- commands/disk/dcomp.cmd --> | Specific | Vanilla CP/M-86 1.1, specific CCP/M-86 3.1 and specific CDOS 4.1 only. |
| DCOPY.CMD <!-- commands/disk/dcopy.cmd --> | Specific | Vanilla CP/M-86 1.1, specific CCP/M-86 3.1 and specific CDOS 4.1 only. |
| DREDIX.CMD <!-- commands/dredix/dredix.cmd --> | 4.1 |  |
| DSKMAINT.CMD <!-- commands/dskmaint/dskmaint.cmd --> | Specific | Specific CDOS 4.1 only. Exact OS-version guard; added formats have no XIOS capability guard. |
| DSP.CMD <!-- commands/dsp/dsp.cmd --> | 4.1 |  |
| ECHO.CMD <!-- commands/echo/echo.cmd --> | Degraded | 3.1 baseline. Without loader support for TAIL=KEEP, text may arrive uppercased; output still works. |
| ED.CMD <!-- commands/ed/ed.cmd --> | Adaptive |  |
| EDITMENU.CMD <!-- commands/editmenu/editmenu.cmd --> | 4.1 |  |
| ERA.CMD <!-- commands/era/era.cmd --> | 3.1 |  |
| ERAQ.CMD <!-- commands/era/eraq.cmd --> | 3.1 |  |
| ERASE.EXE <!-- commands/erase/erase.exe --> | DOS 1.0 + native BDOS | Also requires native Concurrent BDOS calls: will not work under plain DOS 1.0/2.0. |
| FUNCTION.CMD <!-- commands/function/function.cmd --> | 4.1 |  |
| GENCCPM.CMD <!-- commands/genccpm/genccpm.cmd --> | 3.1 |  |
| GENCMD.CMD <!-- commands/gencmd/gencmd.cmd --> | Adaptive | 3.1 baseline. Version-gated BDOS 108 exit-status reporting; normal operation does not require it. |
| GENLDR.CMD <!-- commands/genldr/genldr.cmd --> | 3.1 |  |
| HDMAINT.CMD <!-- commands/hdmaint/hdmaint.cmd --> | 4.1 |  |
| HELP.CMD <!-- commands/help/help.cmd --> | 4.1 |  |
| HEXCOM.CMD <!-- commands/hexcom/hexcom.cmd --> | 3.1 |  |
| INITDIR.CMD <!-- commands/initdir/initdir.cmd --> | 3.1 |  |
| LOADCCPM.COM <!-- commands/loadccpm/loadccpm.com --> | DOS 2.0 |  |
| MKDIR.CMD <!-- commands/mkdir/mkdir.cmd --> | 4.1 |  |
| N.CMD <!-- commands/n/n.cmd --> | 4.1 |  |
| PATH.CMD <!-- commands/path/path.cmd --> | Specific | Specific CDOS 4.1 PCTMP environment API (0Ah). No safe pre-call capability guard; behaviour on the vanilla dispatcher is unpredictable. |
| PIP.CMD <!-- commands/pip/pip4.cmd --> | Adaptive |  |
| PRINT.CMD <!-- commands/print/print.cmd --> | 3.1 |  |
| PRINTMGR.CMD <!-- commands/printmgr/printmgr.cmd --> | 4.1 |  |
| GET.CMD <!-- commands/putget/get.cmd --> | Adaptive | 3.1 baseline. Probes DOS stream support and refuses unsupported DOS redirection; native redirection remains available. Without TAIL=KEEP support, command-tail case is lost. |
| PUT.CMD <!-- commands/putget/put.cmd --> | Adaptive | 3.1 baseline. Probes DOS stream support and refuses unsupported DOS redirection; native redirection remains available. Without TAIL=KEEP support, command-tail case is lost. |
| RDR.CMD <!-- commands/putget/rdr.cmd --> | Adaptive | 3.1 baseline. Probes DOS stream support and refuses unsupported DOS redirection; native redirection remains available. Without TAIL=KEEP support, command-tail case is lost. |
| REDOS.COM <!-- commands/redos/redos.com --> | DOS 2.0 |  |
| REN.CMD <!-- commands/ren/ren.cmd --> | 3.1 |  |
| REN.EXE <!-- commands/rename/ren.exe --> | DOS 1.0 + native BDOS | Also requires native Concurrent BDOS calls: will not work under plain DOS 1.0/2.0. |
| RMDIR.CMD <!-- commands/rmdir/rmdir.cmd --> | 4.1 |  |
| SDIR.CMD <!-- commands/sdir/sdir.cmd --> | 3.1 |  |
| SET.CMD <!-- commands/set/set.cmd --> | Degraded | 3.1 baseline. FAT HIDDEN is unavailable without BDOS 230; FAT NAME is unavailable without FAT label-write support. Cross-version behaviour awaits regression. |
| SETENV.CMD <!-- commands/setenv/setenv.cmd --> | Specific | Specific CDOS 4.1 PCTMP environment API (0Ah). No safe pre-call capability guard; behaviour on the vanilla dispatcher is unpredictable. |
| SETPORT.CMD <!-- commands/setport/setport.cmd --> | 4.1 |  |
| SETUP.CMD <!-- commands/setup/setup.cmd --> | 4.1 |  |
| SHOW.CMD <!-- commands/show/show.cmd --> | Degraded | 3.1 baseline. FAT label reporting is unavailable without FAT support and can miss existing labels with older enumeration. Cross-version behaviour awaits regression. |
| SPL.CMD <!-- commands/spl/spl.cmd --> | 3.1 |  |
| STOP.CMD <!-- commands/stop/stop.cmd --> | 3.1 |  |
| SUBMIT.CMD <!-- commands/submit/submit.cmd --> | 3.1 |  |
| SYSDISK.CMD <!-- commands/sysdisk/sysdisk.cmd --> | 4.1 |  |
| SYSTAT.CMD <!-- commands/systat/systat.cmd --> | 3.1 |  |
| TREE.CMD <!-- commands/tree/tree.cmd --> | 4.1 |  |
| TYPE.CMD <!-- commands/type/type.cmd --> | 3.1 |  |
| WINDOW.CMD <!-- commands/window/window.cmd --> | 3.1 |  |
| WMENU.CMD <!-- commands/window/wmenu.cmd --> | 3.1 |  |
| BACK.CMD <!-- extra/back.cmd --> | 4.1 |  |
| BRINST.CMD <!-- extra/brinst.cmd --> | 4.1 |  |
| CARDFILE.CMD <!-- extra/cardfile.cmd --> | 4.1 |  |
| DRTALK.EXE <!-- extra/drtalk.exe --> | 4.1 |  |
| FM.CMD <!-- extra/fm.cmd --> | 4.1 |  |
| REST.CMD <!-- extra/rest.cmd --> | 4.1 |  |

DOS API levels: [Microsoft MS-DOS Encyclopedia, System Calls](https://www.pcjs.org/documents/books/mspl13/msdos/encyclopedia/section5/).
