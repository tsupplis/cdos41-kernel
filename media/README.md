# Concurrent DOS 4.1 media

Eight 320 KB images and two 1.44MB images are built locally.
The 320K recipes generate an empty filesystem with mk320.py, populate it,
then twist to physical track order. The 1.44MB recipe uses mkfs.cpm and the
same source-built boot sector/loader, without the 320K twist.
All disks include PIP.CMD. System, maintenance and consolidated disks boot.

| Image | Bootable | Contents |
| --- | --- | --- |
| cdos86.img | Yes | Kernel, BATCH, ERA/ERAQ, CHDIR/MKDIR/RMDIR, REN, DATE, SDIR, SHOW, SET, TYPE, DIR, ED, STOP and PIP. |
| cdostools.img | No | SUBMIT, TREE, ECHO.CMD, HELP/HLP, SYSTAT, CHSET, WINDOW/WMENU, PUT/GET/RDR, ERA and PIP. |
| cdosdev.img | No | ASM80/ASM86, DDT86, GENCMD, GENCCPM, GENLDR, HEXCOM, ED, SUBMIT and PIP. |
| cdosmaint.img | Yes | Kernel, SYSDISK, ERA, DSKMAINT, HDMAINT and INITDIR, plus PIP. |
| cdosmenu.img | No | SPL, PRINT, DREDIX, COPYMENU, EDITMENU, PRINTMGR, DSP, menu/terminal data, window BAT examples, sample text and PIP. |
| cdosdos.img | No | SETENV.CMD, COPY.EXE, DATE.EXE, ERASE.EXE, PATH.CMD, TIME.EXE, REN.EXE, LOADCCPM.COM and REDOS.COM, plus PIP. |
| cdosextras.img | No | BACKREST commands, CARDFILE, DRTALK and their support files, plus PIP. |
| cdosadmin.img | No | FUNCTION, DCOPY/DCOMP, SETPORT, SETUP, STOP, CHKCPMFS, N with NATIONAL.MSG, FM with FM.CFG and TERM.DAT, plus PIP. |
| `cdos86-1440.img` | Yes | 1.44MB consolidated system, tools, development, maintenance, DOS and administration contents; EDITMENU and legacy extras remain on their 320K disks |
| `cdosdev-1440.img` | No | 1.44MB development companion: native assembler/linker/librarian/debugger and BASIC compiler tools, DOS Microsoft assembler/linker/librarian, source-built development commands and PIP; no MBASIC |

The consolidated 1.44MB images are included in `disks.zip` by root `make dist`.
They use the native FEAT-compatible CP/M layout (`cpm86-1440` in diskdefs),
not FAT. Use cpmtools with `-T raw -f cpm86-1440` directly; do not apply
`cpm86twist.py`. All files are in user 0; system images mark BATCH SYS.
The development companion is a data disk: boot a system image in A: and
mount it in B:. DOS tools require PC-MODE on CCP/M or CDOS. Neither
MBASIC.CMD nor MBASIC.COM is included on the development companion.

Rebuilt command outputs are used wherever available. Remaining original
binaries and data are explicit base/ prerequisites in the Makefile; there
are no wildcard copies or dependencies on another project.

The tools disk carries HELP.CMD and the maintained HELP.HLP.

`cdos86.cfg` sets the PCE escape key to F12; PCE's default Esc prefix would
swallow Esc and turn the following key release into an emulator command.

`make check` (or `make check-media`) extracts every selected payload and
compares all source bytes, allowing only CP/M record padding. It also checks
image sizes, boot code and loader contents for all ten disks. `make test` runs the same
PCE launcher/configuration convention as CCP/M, with system/tools on A:/B:.
The default adapter is VGA; `./cdos86 cga` selects CGA. `make check-pce` uses
disposable system/tools copies for the shell and keyboard regression.

From the project root, `make dist` copies the ten images to the root and
creates disks.zip with both license files and the project/command/patch notes.
`make check-dist` checks that disk archive. Source distribution stays in Git.
`make clean` removes generated media/releases, including the locally generated
base images; source and OEM inputs remain.
