# !!!WIP!!! Concurrent DOS 4.1 kernel and commands

Independent source rebuild of the OEM Concurrent DOS 4.1 distribution.
The layout follows the CCP/M kernel project: `kernel/con`, `kernel/rsp1`,
`kernel/rsp2`, `kernel/rsp3`, `kernel/sysgen`, and one directory per command.
No build rule reads another project or the historical source archive.

## Build

```sh
make                 # commands, kernel, CCPM.SYS, boot track and two disk images
make check           # command regressions, system headers, boot track and media checks
make check-pce       # headless PCE shell, editing/recall, console shortcuts and PIP copy
make test            # launch the initial system in PCE, as in the CCP/M project
make xios-alt        # optional modular OEM XIOS; currently blocked below
make clean
```

The assembler/linker tools are `cpm86_asm86`, `cpm86_gencmd`,
`pcdev_rasm86`, `pcdev_linkcmd`, `pcdev_linkexe` and `cmdinfo`. C uses `drccpm_cc` and
`drccpm_link`. PL/M uses the same Intel tools as the previous project:
`intel_plm86`, `intel_asm86`, `intel_link86`, `intel_loc86`, `intel_oh86`.
INITDIR uses `drplicpm_pc`, `drpli_objfix` and `drplicpm_link`, following
the CCP/M PL/I build recipe. Standard C headers/runtime come from the
installed toolchain.

Historical source bytes retain DOS line endings and EOF padding. DATE.EXE
has a documented short-year fix; its original and current hashes are recorded. Makefiles check assembler/compiler/linker diagnostics because some
historical tools return success after an error. Included local sources are
normal prerequisites. The PIP 4.1 implementation is retained, with a 4.1N banner; its Makefile builds only
`pip4.cmd`. The unused PIP3 source, target and outputs were removed.
The two license files are unchanged copies of the previous project's files.

## Verified components

| Output | Sources | Historical disk |
| --- | --- | --- |
| `kernel/con/sup.con` | SUP plus supervisor modules and shared definitions | 01 |
| `kernel/con/rtm.con` | RTM, scheduler, flags/queues, ABORT.RTM, 8087 support | 01, 03 |
| `kernel/con/cio.con` | CIO, console, character and auxiliary I/O | 01 |
| `kernel/con/mem.con` | MEM, CP/M memory, shared memory and allocation modules | 01 |
| `kernel/con/sysdat.con` | SYSDAT and shared initialized data | 01 |
| `kernel/con/bdos.con` | PCBDOS, BLACK, FILE1..5 and BDOS definitions | 01, 02 |
| `kernel/con/xios.con` | SQUID IBM PC/XT/AT XIOS and X*.LIB modules | 05 |
| `kernel/rsp1/pin.rsp` | PIN.PLM, RHPIN and PXIOS | 01, 02 |
| `kernel/rsp2/clock.rsp` | CLOCK.A86 | 01 |
| `kernel/rsp3/pctmp.rsp` | TMPPC, menus, DOS support MS1/MS2, DMSUBS, WWCALL | 02, 03, 04 |
| `kernel/rsp3/confid.rsp` | RSPDAT, INITRSP, NTERFACE | 04 |
| `commands/genccpm/genccpm.cmd` | GENC1..6 and GENCCPM headers | 04 |
| `commands/pip/pip4.cmd` | Existing 4.1-mode source build, copied intact | carried over |

The local source build has compiled/linked all outputs above. PIN reports
six PL/M warnings and no compilation errors; warning review remains part of
bring-up. These results establish a component build, not a booted system or
byte identity with an OEM release image.

The final system retains GENCCPM's historical filename `ccpm.sys`.
`kernel/sysgen/genccpm.in` selects the seven CON modules and four resident
processes, places the kernel at paragraph 6000h and allocates disk buffers
with the 4.1 wildcard dialog. The Makefile stages only those components in
a fresh directory; `sysgen.log` records the generation transcript.

`boot/` builds the IBM PC floppy boot chain from local source copies.
`media/` now builds seven 320 KB disks following the CCP/M packaging sequence:
cdos86 (bootable system), cdostools, cdosmaint (bootable maintenance), cdosmenu,
cdosdos and cdosoem1/cdosoem2. Every enabled command output is packaged; original
OEM commands/data are selected explicitly where a rebuilt replacement is absent.
See [media/README.md](media/README.md) for the full table and preservation status.

`make test` runs media/cdos86 and cdos86.cfg with system/tools on A:/B:.
`make check` validates every packaged file, boot track and image size.
`make dist` creates root-level image copies, disks.zip and
`dist/cdos86-source.tar.gz`; `make source-dist` can run separately and
`make check-dist` checks the archive containers. Both project licenses accompany
the disk archive. The build and releases use only project-local inputs.

## Enabled command builds

The top-level build includes the OEM 4.1 families and locally imported
CCP/M command builds. Newly imported sources and Makefiles are unchanged unless
noted below; every dependency is local.

- Development: ASM80, ASM86, GENCMD, HEXCOM, SUBMIT, GENCCPM and GENLDR.
- Native file/system tools: PIP 4.1, BATCH, CHDIR, MKDIR, RMDIR, SYSDISK,
  CHSET, INITDIR, ERA/ERAQ, REN, SYSTAT, DATE, SDIR, SHOW, SET, TYPE, DIR,
  ED, FUNCTION, DSKMAINT and DCOPY/DCOMP.
- Editors/menus: DREDIX, COPYMENU, EDITMENU and WINDOW/WMENU.
- Printing: PRINT, PRINTMGR and DSP.
- DOS: LOADCCPM.COM, COPY.EXE, DATE.EXE, ERASE.EXE and PATH.EXE.

`commands/date` builds native DATE.CMD. `commands/datetime` holds the existing
DOS DATE.EXE build and its 54-case regression; TIME.EXE can be added there later.
`commands/era` builds ERA and the unchanged 4.1 ERAQ together using SCD3 and the
4.1 shared includes. ERA's only executable-source adaptation is the same public
entry rename seen in the 4.1 ERAQ source; the ERAQ comparison found no algorithm
changes. See commands/era/README.md for the comparison.

ASM80, REN, SYSTAT, WINDOW/WMENU, native DATE, SDIR, SHOW, HEXCOM, PRINT,
SET, TYPE, DIR, ED and DCOPY/DCOMP were imported unchanged from CCP/M, including
their Makefiles; PRINT adds diagnostic/output checks to its recipe. Existing 4.1 CHSET and the existing SUBMIT copy are retained.
The source-built HELP.HLP uses an unchanged copy of CCP/M HELP.DAT as its initial
text, indexed by native 4.1 HELP.CMD. The indexer runs under EMU2_CPM_VER=4.1.
Some inherited help topics describe CCP/M-specific features; 4.1 text review
and comparison of imported commands with base binaries remain a later task.
The distribution lists every source-built output explicitly; media checks
compare each selected payload, including the original OEM fallbacks.

RMDIR and SYSDISK select the original ZD and SD modes of `D.A86`, using
small new wrappers patterned on CHDIR/MKDIR. D.A86 is a shared module,
not a standalone command. Historical 4.1 program sources remain unchanged except for the documented
DATE.EXE, GENCCPM, PIN input-queue, XIOS cursor/console-shortcut, CIO editor
and PCTMP CLS/USER changes listed in patches.md.

ASM86, GENCMD and SUBMIT use unchanged source/Makefile copies from the CCP/M
project. GENLDR uses its missing SCD2 startup from the CCP/M 3.1 archive.
All dependencies are local; neither project nor archive is read by a build.

`make check` inspects native CMD headers and DOS output formats, runs
GENCMD's existing self-host/reference checks and verifies DSKMAINT's boot
insertion. These are build checks; live 4.1 command behavior is not claimed
as tested. Original compiler warnings are retained, including two PL/M
warnings in the shared maintenance HELP module.

Remaining command gaps:

- HDMAINT is pending the missing flat LBDOS loader; no older loader is
  substituted. Its original 4.1 binary/manual are preserved on cdosoem2.img.
- REDOS implementation source is missing; its original COM is preserved on cdosdos.img.
- Menu utilities' serial-terminal mode needs separate TERM data.

## Source catalog

`SOURCE-MAP.md` maps the command families and genuine gaps. Their local
source directories are populated, but only verified commands are enabled in
`commands/Makefile`. Additional commands will be considered individually against their 4.1
interfaces. Full build adaptations and unresolved inputs are documented there.

`sources.json` records all 399 archive files and the origin/SHA-256 of each
copied source input. Duplicate archive filenames were checked: all duplicate
copies have identical bytes. It is provenance, not a build-time dependency.

CARDFILE, LOAD6300 and COMPAQ are excluded from the command set.

## Optional modular XIOS

Disk 06 provides the CompuPro/OEM modular `cpxios.con` alternative. It is kept
in `kernel/xios`, separate from the IBM SQUID profile. All its assembly
modules compile, but the link currently requests `8087.SIM`, absent from the
archive. The correct native-8087 assembler/linker profile must be established
before enabling it. No 3.1 XIOS or binary has been substituted.

## DATE.EXE year handling

DATE.EXE now uses the native DATE.CMD short-year pivot: 00..77 means
2000..2077 and 78..99 means 1978..1999. Explicit 19xx and 20xx input is
retained; short 19/20 means 2019/2020, and incomplete three-digit years are
rejected. DOS function 2Bh still validates the complete calendar date and
supported range, so mapping 78/79 does not make 1978/1979 valid DOS dates.
The original archived source/hash remains recorded in `sources.json`.

`make -C commands/datetime check` executes 54 cases against the linked EXE
with synthetic DOS/BDOS calls under emu2. Both command-tail and interactive
paths are covered, including 00/77/78/99, 19/20, explicit four-digit years,
2000-02-29 and malformed years. The harness captures function 2Bh rather
than changing a clock. It rejects the original unmodified DATE.EXE at
`1/2/00`. The top-level `make check` runs this regression check too.

GENCCPM applies the existing CCP/M workaround for DRC 1.11's `char = -1`
miscompilation. It emits each RTM flag as FF FF FF and uses literal FF for
true byte settings. The old output was 00 FF FF, an invalid waiter pointer.
`tools/sysgen_check.py` rejects that table before accepting CCPM.SYS and
also checks the resident-process chain and conventional-memory bounds.
Original/current hashes for these source changes are retained in sources.json.

`patches.md` records only changes made for the 4.1 rebuild, including the
DATE/GENCCPM fixes and the local PIN queue/cursor corrections. The former
alternating-key loss was two consoles sharing VINQ000; PIN now creates a
separate input queue for each console. See `make check-pce` for the live
single-keystroke, line-editing, console-switch and shell regressions, and
`make check` for the built-cursor fixtures.

Function 10 editing follows the CCP/M port: Ctrl-A/F move left/right,
Ctrl-B toggles Home/End, Ctrl-G deletes, Ctrl-K/X remove the suffix/prefix,
and Ctrl-W recalls the last nonempty line on an empty input (otherwise End).
Left/Right, Home/End, Delete and Up work during buffered input; Up is Ctrl-W.
Recall is per console. Ctrl-U clears with #/newline, Ctrl-R retypes and Ctrl-E
continues on a new row. Ctrl+Alt+1..4 selects consoles; Ctrl+Alt+Tab cycles.

CLS is a shell built-in. USER reports the user number without the media note.
Both images include the unchanged source-built 4.1 SYSDISK.CMD: `SYSDISK`
displays the system search path, `SYSDISK [OFF]`/`[ON]` disables/enables it,
and a path argument sets it. It retains the local DOS-directory support.

`DEL` invokes native ERA.CMD in both PCTMP and BATCH. System, tools, maintenance and DOS images
include ERA.CMD; `DELQ` continues to invoke ERAQ.CMD. See ccp.md for aliases.
