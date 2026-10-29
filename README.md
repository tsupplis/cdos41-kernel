# Concurrent DOS 4.1 Kernel and Tools

**Early work in progress — boots from floppy images.**

This project preserves Digital Research's Concurrent DOS 4.1 multitasking OS,
including PC-MODE, as a usable, rebuildable system for running and exploring
classic 16-bit software. Runnable disks, development tools and patch notes
accompany the sources, with CP/M-Plus-style usability improvements.

| Goal | Distribution |
| --- | --- |
| Source rebuild | Kernel, four RSP families, boot sources and command tools |
| Usability improvements | Command-line editing and recall, console shortcuts, paging and CLS |
| Additional tools | ASM80, HEXCOM, DREDIX, WINDOW/WMENU and floppy copy/compare commands |
| Date fixes | Patched native date/reporting utilities and corrected short-year input in DATE.EXE |
| OEM preservation | Original utilities and support data retained where a rebuilt replacement is pending |

The build follows the CCP/M project's source organization and toolchain.
All build inputs are local to this repository. [Source pedigree and component
status](source-map.md) and `sources.json` record the origins and source hashes.

## CP/M-Plus usability improvements

The current version includes:

- CP/M-Plus-style command-line cursor movement, insertion, deletion and recall.
- Left/Right, Home/End, Delete and Up during buffered console input.
- Ctrl+Alt+1–4 to select consoles; Ctrl+Alt+Tab to cycle through them.
- Optional paging for TYPE, SDIR and DIR.CMD, alongside the built-in DIR's `/P`.
- CP/M-Plus-style console redirection through PUT, GET and RDR for native commands.
- A built-in CLS command and a common `Press any key to continue...` prompt.
- DEL mapped to native ERA.CMD in both the shell and BATCH.

## Command line conveniences

Buffered console input supports editing and recall of the last nonempty line
on each console:

| Key | Action |
| --- | --- |
| Left / Ctrl-A | Move one character left |
| Right / Ctrl-F | Move one character right |
| Home / End | Go to the beginning / end |
| Up / Ctrl-W | Recall the last line when empty; otherwise go to the end |
| Backspace / Rubout | Delete left of the cursor |
| Delete / Ctrl-G | Delete at the cursor |
| Ctrl-K / Ctrl-X | Delete to the right / left of the cursor |
| Ctrl-B | Toggle between beginning and end |
| Ctrl-U / Ctrl-R | Cancel the line / retype it on a new line |

Return accepts the whole line from any cursor position. The editor also
serves applications using BDOS Function 10; raw-input applications keep
their own keys. There is one saved line per console, not a history list.
Ctrl-U retains the historical #/newline echo; Ctrl-E continues on a new row.

| Command | Effect |
| --- | --- |
| `CLS` | Clear the screen and home the cursor |
| `TYPE filespec [PAGE]` / `[PNN]` | Page text; NN selects 01..23 rows |
| `SDIR [PAGE]` | Page a detailed directory listing |
| `DIR.CMD filespec [P]` | Page the standalone directory command |
| `DIR filespec /P` | Page the shell's built-in directory listing |
| `ORDER` | Display the executable-extension search order |
| `ORDER CMD,COM,EXE,BAT` | Set the extension search order |
| `SYSDISK` | Display the system search path |
| `SYSDISK [ON]` / `[OFF]` | Enable / disable system-path searching |
| `SYSDISK path` | Set the system search path |

Optional paging uses 23 screen rows. Press a key to continue or Ctrl-C to stop;
paging is off by default. TYPE and SDIR count tabs and wrapped text. SDIR's
`[LENGTH=n]` controls repeated headers separately. The standalone DIR.CMD
and built-in DIR retain their respective option syntax.

`ORDER` provides command-order configuration in 4.1. SETDEF will not be ported;
system-path configuration remains with SYSDISK.

See [the shell command and alias table](ccp.md) and `HELP` for command syntax.
HELP on the tools disk uses the imported CCP/M text as a starting point;
the second OEM disk retains the original 4.1 help text.

`PUT`, `GET` and `RDR` redirect a native program's console output, input or
both, using a bracket prefix:

| Command | Effect |
| --- | --- |
| `PUT [out{,A}{,E\|EO}] cmd` | Capture output; `A` appends, `E`/`EO` also echoes it |
| `GET [in{,E\|EI}] cmd` | Read input from a file; `E`/`EI` echoes it |
| `RDR [in,out{,A}{,E\|EI\|EO}] cmd` | Redirect input and output together |

```text
A>PUT [LIST.TXT] SDIR.CMD *.CMD
A>GET [KEYS.IN] PIP.CMD
A>RDR [KEYS.IN,PIP.LOG] PIP.CMD
```

The current tools support native `.CMD` programs using BDOS console calls.
Use DIR.CMD or SDIR.CMD for directory capture. The shell's built-in commands,
DOS executables, BIOS video calls and direct screen writes are outside this
mechanism. [PUT/GET/RDR notes](commands/putget/README.md).

## Distributions

| Image | Bootable | Contents |
| --- | --- | --- |
| `cdos86.img` | Yes | Kernel, core file commands, ED, DATE, SDIR, SET, SHOW, SUBMIT, BATCH, SYSDISK, ERA/ERAQ, PUT/GET/RDR, PIP and shell alias targets |
| `cdostools.img` | No | ASM80/ASM86, GENCMD, GENCCPM, HEXCOM, HELP, PRINT, SYSTAT, CHSET, GENLDR, LOADCCPM, WINDOW/WMENU and core commands |
| `cdosmaint.img` | Yes | Kernel, DSKMAINT, DCOPY, DCOMP, INITDIR, BATCH, SYSDISK, ERA and PIP |
| `cdosmenu.img` | No | DREDIX, COPYMENU, EDITMENU, PRINTMGR, DSP, menu/terminal data, BAT examples and PIP |
| `cdosdos.img` | No | COPY.EXE, DATE.EXE, ERASE.EXE, PATH.EXE, original TIME.EXE, REN.EXE and REDOS.COM, core commands and PIP |
| `cdosoem1.img` | No | Original backup/file-manager tools, their support files and PIP |
| `cdosoem2.img` | No | FUNCTION, HELP, original configuration/maintenance tools, HDMAINT and its manual, original 4.1 help text and PIP |

`make dist` places these seven images and `disks.zip` at the repository root.
Source distribution and history stay in Git.

Boot the system or maintenance disk in A: and use the data disks in B:.
`make test` launches PCE with system/tools mounted on A:/B:. HELP and
WINDOW/WMENU are on the tools disk; use `B:HELP` with the desired help disk
inserted. The kernel retains its historical `CCPM.SYS` filename.

320 KB: **untwist → cpmtools `ccpm86-320` → twist**.
The filesystem and boot track are generated locally.
[Media recipes, contents and emulator usage](media/README.md).

## Kernel and resident components

| Component | Purpose | Origin |
| --- | --- | --- |
| SUP | Supervisor and native command dispatch | Recompiled from CDOS 4.1 and adapted |
| RTM | Scheduling, queues, flags and process control | Recompiled from CDOS 4.1 |
| CIO | Console, character and auxiliary I/O | Recompiled from CDOS 4.1 and adapted |
| MEM | Memory allocation and shared memory | Recompiled from CDOS 4.1 |
| BDOS | File and filesystem services | Recompiled from CDOS 4.1 |
| SYSDAT | Shared system data | Recompiled from CDOS 4.1 |
| XIOS | IBM PC/XT/AT SQUID hardware support | Recompiled from CDOS 4.1 and adapted |
| PIN | Physical console input | Recompiled from CDOS 4.1 and adapted |
| CLOCK | Timekeeping resident process | Recompiled from CDOS 4.1 |
| PCTMP | Shell and command execution | Recompiled from CDOS 4.1 and adapted |
| CONFID | Resident configuration support | Recompiled from CDOS 4.1 |
| Boot sector / loader | Start the generated kernel | Recompiled from CCP/M-86 boot sources |

## Commands

Origin terminology follows [ccpm86-kernel](../ccpm86-kernel/README.md).
**Original** identifies an OEM reference binary in `base/`; rebuilt commands
are packaged wherever available. Imported source builds retain their existing
patches; comparison with the corresponding 4.1 binaries continues incrementally.
**Adapted for parity** identifies imports reviewed and adapted against 4.1
behavior; intentional extensions are documented with each command.

Compatibility details live with each tool: [SDIR](commands/sdir/README.md)
covers DOS directories and options; [TYPE](commands/type/README.md) covers
DOS EOF, passwords and bracketed paging; [SHOW](commands/show/README.md)
covers disk/user/label reporting and DOS-media restrictions.

| Tool | Purpose | Binary (`base/`) | Source (`commands/`) |
| --- | --- | --- | --- |
| `asm80` | 8080 assembler | — | Translated using XLT86 from CP/M-80 2.2 and adapted |
| `asm86` | 8086 assembler | — | Recompiled from CCP/M-86 3.1 and adapted |
| `batch` | Run BAT command files | — | Recompiled from CDOS 4.1 and adapted |
| `chdir / mkdir / rmdir` | Change, create or remove directories | — | Recompiled from CDOS 4.1; shared D.A86 implementation |
| `chset` | Inspect or change CMD header flags | — | Recompiled from CDOS 4.1 |
| `cls` | Clear the terminal screen | — | New; TMP built-in; VT52 ESC-E |
| `copy.exe` | Copy files | — | Recompiled from CDOS 4.1 |
| `copymenu` | Copy menu definitions | — | Recompiled from CDOS 4.1 |
| `date` | Display or set the date | — | Recompiled from CCP/M-86 3.1 and adapted, Y2K patched |
| `date.exe` | Display or set the date through DOS | — | Recompiled from CDOS 4.1 and adapted, short-year fix; commands/datetime |
| `dcomp / dcopy` | Compare or copy floppy diskettes | — | Ported from PC DOS 1.10; imported from CCP/M-86 |
| `dir` | List directory contents | — | Recompiled from CCP/M-86 3.1 and adapted; separate CDOS 4.1 TMP built-in |
| `dredix` | Full-screen text editor | — | Recompiled from CDOS 4.1 |
| `dskmaint` | Format, verify and copy diskettes | — | Recompiled from CDOS 4.1 |
| `dsp` | Inspect print-spool information | — | Recompiled from CDOS 4.1 |
| `ed` | Line-oriented text editor | — | Recompiled from CCP/M-86 3.1 and adapted |
| `editmenu` | Edit menu definitions | — | Recompiled from CDOS 4.1 |
| `era / eraq` | Erase files, optionally with confirmation | ERA only | ERA recompiled from CCP/M-86 3.1 and adapted; ERAQ recompiled from CDOS 4.1 |
| `erase.exe` | Erase files through DOS | — | Recompiled from CDOS 4.1 |
| `function` | Program function keys | — | Recompiled from CDOS 4.1 |
| `gencmd` | Convert H86 output into CMD executables | — | Recompiled from CCP/M-86 3.1 and adapted |
| `get` | Feed console input from a text file | — | New; shared putget.lib engine, imported from the CCP/M project |
| `genccpm` | Generate and configure the system image | — | Recompiled from CDOS 4.1 and adapted; flag-table fix |
| `genldr` | Generate a system loader | — | Recompiled from CDOS 4.1; carried-over SCD2 startup |
| `hdmaint` | Hard-disk maintenance | Original | 4.1 source present; build pending the missing flat LBDOS loader |
| `help / help.hlp` | Browse indexed command help | HLP only | Recompiled from CDOS 4.1; help.dat imported from CCP/M-86 |
| `hexcom` | Convert Intel HEX to COM binaries | — | HEXCOM 3.00-compatible C from [tpzasm](https://github.com/johnsonjh/tpzasm) |
| `initdir` | Enable or remove directory date/time stamps | — | Recompiled from CDOS 4.1 |
| `loadccpm.com` | Load the system from DOS | — | Recompiled from CDOS 4.1 |
| `path.exe` | Display or set the DOS search path | — | Recompiled from CDOS 4.1 |
| `pip` | Copy and transfer files | — | Recompiled from CDOS 4.1 and adapted |
| `print` | Print files using Concurrent printer services | — | Recompiled from CCP/M-86 3.1 |
| `printmgr` | Manage print spooling | — | Recompiled from CDOS 4.1 |
| `put` | Capture console output into a file | — | New; shared putget.lib engine, imported from the CCP/M project |
| `rdr` | Redirect console input and output together | — | New; shared putget.lib engine, imported from the CCP/M project |
| `redos.com` | Return from Concurrent to DOS | Original | —; original OEM binary retained, implementation source missing |
| `ren` | Rename files | Original | Recompiled from CCP/M-86 3.1 and adapted |
| `sdir.cmd` | Detailed, sorted directory listing | Original | Recompiled from CCP/M-86 3.1 and adapted for parity |
| `set` | Set file and drive attributes | Original | Recompiled from CCP/M-86 3.1 and adapted |
| `setup` | Customize system hardware settings | Original | —; original OEM binary retained |
| `show.cmd` | Display disk space and drive information | Original (3.3) | Recompiled from CCP/M-86 3.1 and adapted for parity |
| `submit` | Run SUB command files | — | Recompiled from CCP/M-86 3.1 and adapted |
| `sysdisk` | Display or change the system search path | — | Recompiled from CDOS 4.1; SD-mode D.A86 wrapper |
| `systat` | Inspect processes and system resources | Original | Recompiled from CCP/M-86 3.1 and adapted |
| `time.exe` | Display or set the time through DOS | Original | Reverse Engineered from CDOS 4.1 |
| `type.cmd` | Display a text file | Original (3.2) | Recompiled from CCP/M-86 3.1 and adapted for parity |
| `window` | Control console windows from commands | Original | C rewrite; shared modules in commands/window |
| `wmenu` | Interactive console-window manager | Original | C rewrite; shared modules in commands/window |

ERA and ERAQ share `commands/era`, using the 4.1 startup and includes. The two
ERAQ versions have the same query/delete logic; ERA adopts the 4.1 entry-name
convention. [ERA/ERAQ notes](commands/era/README.md).

WINDOW and WMENU share the C implementation carried over from CCP/M.
The redundant `base/ed.cmd`, `base/submit.cmd` and `base/dir.cmd` references
were removed. ED and SUBMIT match archived pre-4.1 Concurrent distributions;
DIR has the same instruction flow as a rebuild of the CCP/M 3.1 source,
with different linked data/stack addresses. Media uses their maintained local
source builds; the current DIR also includes optional paging. DIR.CMD remains
separate from the native 4.1 shell's built-in DIR.

Original program copies rebuilt from local CDOS 4.1 sources have also been
removed from `base/`; media uses the corresponding `commands/` outputs.
HDMAINT is the exception while its loader work remains pending. Original help
data and references for commands still undergoing review remain available.
Removed-binary hashes and replacement paths are recorded in `sources.json`.

PRINT is rebuilt from its original C sources and historical module list;
its recipe validates compiler/linker diagnostics and the resulting CMD.
[WINDOW/WMENU notes](commands/window/README.md) · [PRINT notes](commands/print/README.md).

### Original OEM utilities

The OEM disks also preserve BACK, REST, BRINST, FM, SPL, DISKSTAT, N,
SETPORT and STOP, with their support data. REN.EXE is retained
for the shell's RENAME alias. These remain **Original** binaries while the
corresponding source work is considered individually.
[Complete disk contents](media/README.md) · [Source map](source-map.md).

## Y2K utilities

The native DATE, SDIR and SHOW imports retain the CCP/M project's date fixes.
DOS DATE.EXE has the same short-year pivot as native DATE.CMD: 00–77 maps to
2000–2077 and 78–99 to 1978–1999, subject to DOS calendar validation.
The regression runs 54 command-line/interactive cases without changing a clock.
Native DATE.CMD is in `commands/date`; DOS DATE.EXE and its tests are in
`commands/datetime`. TIME.EXE has been reconstructed as `pctime.a86`; its
behavioral verification and replacement of the packaged OEM binary are pending.

## Kernel and RSP patches

[Patch notes](patches.md) cover buffered line editing, per-console recall,
console shortcuts, adapter-aware cursor shape, PIN's separate input queues,
GENCCPM flag initialization, date handling, CLS and the DEL/PAUSE changes.
Only changes made for this 4.1 rebuild are recorded there.

The IBM SQUID XIOS is the selected build. The alternative modular OEM XIOS
is preserved separately; its link still needs the missing 8087.SIM input/profile.
HDMAINT's source build awaits its flat LBDOS loader; its original binary and
manual remain available on the second OEM disk. HELP text and imported commands
will be aligned with the original 4.1 distribution progressively.

## Build and checks

Build: [cpm86-crossdev](https://github.com/tsupplis/cpm86-crossdev), make,
cpmtools, Python 3 and zip. The Makefiles use the installed `cpm86_*`,
`pcdev_*`, Intel PL/M, DRC and PL/I tools; emu2 runs the build-time programs.
The boot build also uses `h862bin` from cpm86-cmdtools. PCE runs the interactive
system and the live regression checks.

| Command | Result |
| --- | --- |
| `make` | Commands, kernel/RSPs, boot sources and seven images |
| `make check` | Command headers, DATE parser, system layout, cursor, boot track and every packaged file/size |
| `make check-pce` | Boot, console switching, line editing/recall, DIR, PIP, CLS, USER and SYSDISK |
| `make check-type` | OEM/rebuilt TYPE comparison, DOS/CP/M EOF, passwords and paging |
| `make check-show` | OEM/rebuilt SHOW comparison, media guards, capacity/free space, users and labels |
| `make check-sdir` | OEM/rebuilt SDIR comparison on CP/M/FAT12, directory markers/counts, options and paging |
| `make check-redirection` | PUT capture/append, GET/RDR input, copied bytes and return to shell |
| `make check-aliases` | TMP/BATCH DEL execution, argument preservation and common PAUSE text |
| `make test` | Launch PCE with system/tools disks on A:/B: |
| `make dist` | Root-level disk images and disks.zip |
| `make check-dist` | Build and verify the disk archive |
| `make clean` | Remove generated build outputs, media and releases |

[Source pedigree](http://www.cpm.z80.de) · [License correspondence](LICENSE.md).

## Companion projects

| Project | Description |
|---------|-------------|
| [cpm86-kernel](https://github.com/tsupplis/cpm86-kernel)     | CP/M-86 1.1 distribution rebuilt from patched and reconstituted sources |
| [ccpm86-kernel](https://github.com/tsupplis/ccpm86-kernel)         | CCP/M-86 3.1 distribution rebuilt from patched and reconstituted sources |
| [cdos41-kernel](https://github.com/tsupplis/cdos41-kernel)         | Concurrent DOS 4.1 distribution rebuilt from patched and reconstituted sources |
| [cpm86-crossdev](https://github.com/tsupplis/cpm86-crossdev) | Unix CP/M-86 cross development project (compilers, emulation and tools) |
| [cpm86-hacking](https://github.com/tsupplis/cpm86-hacking)   | CP/M-86 miscellaneous tools and PCE emulator helpers |
| [cpm86-cmdtools](https://github.com/tsupplis/cpm86-cmdtools) | CP/M-86 `.cmd` file manipulation tools |
| [cpm86-ports](https://github.com/tsupplis/cpm86-ports)       | CP/M-86 application ports in C and assembler |
| [cpm86-vi](https://github.com/tsupplis/cpm86-vi)             | STevie vi port for CP/M-86 and PC-DOS |
| [cpm86-msbasic](https://github.com/tsupplis/cpm86-msbasic)   | A recreaction of msbasic-86 for CP/M-86 and PC-DOS 1.1 from gwbasic sources |
| [cpm86-menu](https://github.com/tsupplis/cpm86-menu)   | A submit replacement and a menu system for submit orchestration for CP/M-86 1.1 |
| [cpm86-make](https://github.com/tsupplis/cpm86-make)   | A simple submit based make tool for CP/M-86 |
| [pcdos11-hacking](https://github.com/tsupplis/pcdos11-hacking) | PC-DOS 1.1 distribution, tools and notes |

--

## License

CP/M-derived material is covered by the [CP/M license](LICENSE.md); other material uses the [MIT license](LICENSE-bis.md), unless specified otherwise in a subdirectory.
