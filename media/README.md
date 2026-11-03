# Concurrent DOS 4.1 media

Eight physical-CHS 320 KB images are built locally. The layout follows the
CCP/M media workflow: the checked-in base.img template, source-built boot track in
cdos86base.img, then untwist / populate / twist for each distribution disk.
All disks include the rebuilt PIP4 as PIP.CMD. Only the system and maintenance
disks contain CCPM.SYS; the remaining disks are data-only.

| Image | Bootable | Contents |
| --- | --- | --- |
| cdos86.img | Yes | Kernel, BATCH, SYSDISK, ERA/ERAQ, CHDIR/MKDIR/RMDIR, REN, DATE, SDIR, SHOW, SET, SUBMIT, TYPE, DIR, ED, STOP and PIP. |
| cdostools.img | No | TREE, ECHO.CMD, HELP/HLP, SYSTAT, CHSET, WINDOW/WMENU, PUT/GET/RDR, SYSDISK, ERA and PIP. |
| cdosdev.img | No | ASM80/ASM86, DDT86, GENCMD, GENCCPM, GENLDR, HEXCOM, ED, SUBMIT and PIP. |
| cdosmaint.img | Yes | Kernel, SYSDISK, ERA, DSKMAINT, DCOPY, HDMAINT and INITDIR, plus PIP. |
| cdosmenu.img | No | SPL, PRINT, DREDIX, COPYMENU, EDITMENU, PRINTMGR, DSP, menu/terminal data, window BAT examples, sample text and PIP. |
| cdosdos.img | No | SETENV.CMD, COPY.EXE, DATE.EXE, ERASE.EXE, PATH.EXE, TIME.EXE, REN.EXE, LOADCCPM.COM and REDOS.COM, plus PIP. |
| cdosextras.img | No | BACKREST commands, CARDFILE, DRTALK and their support files, plus PIP. |
| cdosadmin.img | No | FUNCTION, DCOMP, SETPORT, SETUP, STOP, CHKCPMFS, N with NATIONAL.MSG, FM with FM.CFG and TERM.DAT, plus PIP. |

Rebuilt command outputs are used wherever available. Remaining original
binaries and data are explicit base/ prerequisites in the Makefile; there
are no wildcard copies or dependencies on another project.

The tools disk carries HELP.CMD and the maintained HELP.HLP.

`cdos86.cfg` sets the PCE escape key to F12; PCE's default Esc prefix would
swallow Esc and turn the following key release into an emulator command.

`make check` (or `make check-media`) extracts every selected payload and
compares all source bytes, allowing only CP/M record padding. It also checks
327680-byte image sizes and all eight boot tracks. `make test` runs the same
PCE launcher/configuration convention as CCP/M, with system/tools on A:/B:.
The default adapter is VGA; `./cdos86 cga` selects CGA. `make check-pce` uses
disposable system/tools copies for the shell and keyboard regression.

From the project root, `make dist` copies the eight images to the root and
creates disks.zip with both license files and the project/command/patch notes.
`make check-dist` checks that disk archive. Source distribution stays in Git.
`make clean` removes generated media/releases, including the locally generated
base images; source and OEM inputs remain.
