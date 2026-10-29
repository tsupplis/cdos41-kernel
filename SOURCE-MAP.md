# Concurrent DOS 4.1 source map

Disk numbers below refer to `41SRC_nn.IMG.DIR` in the historical OEM archive.
All working inputs are copied locally; build rules never access that archive.

## Kernel organization

- **Disk 01:** SUP, RTM, CIO, MEM, SYSDAT and shared DEF/FMT/LIT files;
  CLOCK, PIN interface/startup. `ABORT.RTM` is on disk 03 and is an RTM
  include, not the CCP/M 3.1 ABORT.RSP. PIN source is on disk 02.
- **Disk 02:** PC-MODE BDOS plus BLACK; PCTMP link recipe and interface files.
- **Disk 03:** PCTMP DOS personality (`MS1`, `MS2`), RUNMENU and TMPDIR.
- **Disk 04:** GENCCPM, CONFID initialization RSP and shared TMPMENU.
- **Disk 05:** Monolithic IBM PC/XT/AT SQUID XIOS (selected default).
- **Disk 06:** Alternative modular CompuPro/OEM XIOS. Its SERIN/SEROUT
  modules are XIOS drivers, not the similarly named CCP/M 3.1 RSPs.

Do not assume the old nine-RSP list applies to 4.1. The identified RSP
builds here are PIN, CLOCK, PCTMP and CONFID. Boot/load sources reside among
DSKMAINT, HDMAINT, GENLDR and LOADCCPM on disks 08, 10 and 11.

## Command families

| Directory | Main sources / historical recipe | Status |
| --- | --- | --- |
| `asm86` | Unchanged CCP/M source build and Makefile | Verified build, enabled |
| `gencmd` | Unchanged CCP/M source build, Makefile and reference fixture | Verified build and self-host check, enabled |
| `submit` | Unchanged CCP/M source build and Makefile | Verified build, enabled; live 4.1 execution not yet checked |
| `genccpm` | GENC1..6.C, GENCCPM.BAT (04) | Verified build, enabled |
| `pip` | Copied existing PIP 4.1-mode source/Makefile | Verified build, enabled |
| `batch` | BATCH.A86 + TMPMENU/TMPDIR/TMPMENUE (07) | Verified build, enabled |
| `chset` | MAIN/CHSET/FUNCTION.C, CPMIF.A86 (07) | Verified build, enabled |
| `chdir` | CHDIR/PATH/DERROR.A86 (07) | Verified build, enabled |
| `rmdir` | ZD-mode wrapper plus unchanged D/PATH/DERROR.A86 (07) | Verified build, enabled |
| `sysdisk` | SD-mode wrapper plus unchanged D/PATH/DERROR.A86 (07) | Verified build, enabled |
| `mkdir` | MKDIR/PATH/DERROR.A86 (11/07) | Verified build, enabled |
| `dredix` | C editor modules + UTIL/WMCA/WWCALL, DREDIX.INP (08) | Verified build, enabled |
| `dsp` | DSP/DSPM.C, UTLASM.A86 (09) | Verified build, enabled |
| `eraq` | SCD3.A86 + ERAQ.PLM (09) | Verified build, enabled |
| `help` | SCD3.A86 + HELP3.PLM (11/09) | Verified build, enabled; HELP.DAT absent, HELP.HLP not generated |
| `function` | FUNC1/2/3, screen modules, HELP1/2, FUNC10 (09/10) | Verified build, enabled |
| `dskmaint` | SQUIDDM1/2/3 + screen/help modules (08/09) | Verified build, enabled; DOSBOOT insertion checked |
| `hdmaint` | H70.A86 and HD*.LIB, boot/load sectors (10/11) | Pending: flat LBDOS.H86 absent; no older loader substitution, by decision |
| `initdir` | INITDIR.PLI, INITDIRA/DIOMOD (11) | Verified build, enabled; PL/I recipe/declarations carried over |
| `genldr` | GENLDR/LDRBUF.PLM, GENMSG.A86 (10) | Verified build, enabled; missing SCD2 supplied from CCP/M 3.1 archive |
| `loadccpm` | LOADCCPM.A86 (11) | Verified build, enabled; DOS .COM output |
| `printmgr` | SPOOL/SPOOLM/SNCHECK.C, UTLASM.A86 (11/09) | Verified build, enabled |
| `copymenu` | CMED*.C + screen/window/attribute helpers (07/08/09) | Verified build, enabled |
| `editmenu` | MED*.C + shared screen/window helpers (08/09) | Verified build, enabled |
| `copy` | PCCOPY.A86, COPY.BAT (07) | Verified build, enabled; DOS .EXE output |
| `date` | PCDATE.A86, DATE.BAT (08) | Verified build, enabled; DOS .EXE output |
| `erase` | PCERASE/MEDIA.A86, ERASE.BAT (09) | Verified build, enabled; DOS .EXE output |
| `path` | PATHX.A86, PATH.BAT (11) | Verified build, enabled; DOS .EXE output |
| `d` | D.A86 + PATH/DERROR (07) | Shared implementation for CHDIR/MKDIR/RMDIR/SYSDISK; no D executable |
| `redos` | REDOS.SUB (11) | Blocked: REDOS.A86 missing |

CARDFILE, LOAD6300 and COMPAQ are intentionally excluded from this project.
Their original archive entries remain in `sources.json` for provenance; no
local source copies or build targets are retained.

## Missing standalone utility sources

This archive does not supply the old native standalone ASM86, DDT86, GENCMD,
ED, SDIR, SET, SHOW, SUBMIT, SYSTAT, TOD, TYPE, VCMODE, CONFIG, SETUP,
WINDOW or WMENU source builds under those names. This is not proof that each
is needed unchanged: some functionality belongs to the 4.1 TMP or new tools.
ASM86, GENCMD and SUBMIT have been copied locally with their existing
Makefiles. The remaining candidates still require individual review against
the actual 4.1 interfaces and distribution requirements.

## Headers and common code

PORTAB.H, STDIO.H and CTYPE.H are supplied by the installed DRC toolchain;
the local CPM.H/CPMFUNC.H and program-specific headers are archived inputs.
Duplicate COMLIT.LIT, TMPDIR.LIB, TMPMENU.LIB, TMPMENUE.LIB and WWCALL.A86
copies are byte-identical. Each build family currently owns the local inputs
its historical recipe needs, following the existing per-command layout.

## Build adaptations and gaps

- INITDIR uses `drplicpm_pc`, `drpli_objfix` and `drplicpm_link`, following
  the existing CCP/M Makefile. Its missing `diomod.dcl` and `initdira.dcl`
  are unchanged local copies from that project; the 4.1 PL/I and assembly
  sources are retained.
- GENLDR's missing `scd2.a86` comes from `ossrc/ccpmv31/D10`, unchanged.
  It exports the reset/PLM and MON1..4 interface required by these sources.
- COPYMENU/EDITMENU retain the original RASM `$nc` option on MENUIO to
  preserve the C symbol spelling. Their serial-terminal mode also needs
  TERM.DAT or TERMx.DAT at runtime; these data files are not supplied here.
- DSKMAINT uses the original link input via a generated input file to avoid
  DOS command-tail truncation. `embed_boot.py` reproduces the original SID
  insertion of DOSBOOT.CMD bytes 80h..27Fh and verifies that all other bytes
  remain unchanged. Extra zero padding in DOSBOOT is deliberately excluded.
- LOADCCPM retains the original `$fi` assembler option, `NHEAD 8080 CODE[B10]`
  conversion, and raw `.COM` output. Its entry JMP is checked at file offset
  zero; using DRI HEX records here would incorrectly retain 256 leading zeros.
- HELP.CMD builds, but the 4.1 HELP.DAT content is absent. No 3.1 text has
  been silently substituted and no HELP.HLP is advertised as built.
- HDMAINT's program and individual loader components assemble under the
  optional `make -C commands/hdmaint components` target. The final command
  remains pending: the recipe requires flat LBDOS.H86, while the supplied
  LBDOS3.A86 is a different relocatable interface. The decision is to leave
  HDMAINT pending rather than substitute the older loader source.
- REDOS lacks its implementation source and remains disabled.

Build/header checks establish compilable local outputs, not OEM byte identity
or runtime compatibility. GENCMD additionally passes its existing self-host
and HELLOB reference checks; DSKMAINT checks its embedding operation.

## DATE.EXE year handling

DATE.EXE now uses the native DATE.CMD short-year pivot: 00..77 means
2000..2077 and 78..99 means 1978..1999. Explicit 19xx and 20xx input is
retained; short 19/20 means 2019/2020, and incomplete three-digit years are
rejected. DOS function 2Bh still validates the complete calendar date and
supported range, so mapping 78/79 does not make 1978/1979 valid DOS dates.
The original archived source/hash remains recorded in `sources.json`.

`make -C commands/date check` executes 54 cases against the linked EXE
with synthetic DOS/BDOS calls under emu2. Both command-tail and interactive
paths are covered, including 00/77/78/99, 19/20, explicit four-digit years,
2000-02-29 and malformed years. The harness captures function 2Bh rather
than changing a clock. It rejects the original unmodified DATE.EXE at
`1/2/00`. The top-level `make check` runs this regression check too.

## Initial system and media

The local sysgen Makefile builds CCPM.SYS from SUP/RTM/CIO/MEM/BDOS/SYSDAT/
XIOS and PIN/CLOCK/PCTMP/CONFID. The response file uses OS start 6000h and
the 4.1 wildcard disk-buffer dialog. The IBM PC boot-sector and loader
sources and cpm86twist.py are unchanged copies from the CCP/M project.
The SQUID 320 KB DPB and reversed head-1 ordering match that boot chain.

The initial media follow the CCP/M base.img -> cdos86base.img -> untwist /
populate / twist pattern. Here base.img is generated with mkfs.cpm rather
than copied as a binary template. cdos86.img contains the system and minimal
commands; cdostools.img is a data-only development disk. `make test` uses
media/cdos86 and cdos86.cfg, adapted from the CCP/M launcher/configuration
with the two local image names and two drives. Build rules read no sibling
project. HDMAINT's missing loader is not on this floppy boot path.
