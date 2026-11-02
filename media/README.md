# Concurrent DOS 4.1 media

Seven physical-CHS 320 KB images are built locally. The layout follows the
CCP/M media workflow: the checked-in base.img template, source-built boot track in
cdos86base.img, then untwist / populate / twist for each distribution disk.
All disks include the rebuilt PIP4 as PIP.CMD. Only the system and maintenance
disks contain CCPM.SYS; the remaining disks are data-only.

| Image | Bootable | Contents |
| --- | --- | --- |
| cdos86.img | Yes | Kernel, native file commands/editor, DATE, SDIR, SET, SHOW, SUBMIT, BATCH, SYSDISK, ERA/ERAQ; Rebuilt REN.EXE and STOP.CMD for shell aliases. |
| cdostools.img | No | ASM80/ASM86, GENCMD, GENCCPM, HEXCOM, HELP/HLP, SYSTAT, CHSET, GENLDR, WINDOW/WMENU, PUT/GET/RDR, SYSDISK, ERA and PIP. |
| cdosmaint.img | Yes | Kernel, DSKMAINT, HDMAINT.CMD, HDMAINT.DOC, DCOPY and core commands. |
| cdosmenu.img | No | SPL, PRINT, DREDIX, COPYMENU, EDITMENU, PRINTMGR, DSP, menu/terminal data, window BAT examples and sample text. |
| cdosdos.img | No | Rebuilt COPY.EXE, DATE.EXE, ERASE.EXE, PATH.EXE, TIME.EXE, REN.EXE and SETENV.EXE; LOADCCPM.COM, rebuilt REDOS.COM and core commands. |
| cdosextras.img | No | INITDIR, BackRest, CARDFILE, DRTALK, their support files and PIP |
| cdosadmin.img | No | BACKREST.DOC, FUNCTION, DCOMP, SETPORT, SETUP, STOP, N with NATIONAL.MSG, FM with FM.CFG and TERM.DAT and PIP |

Rebuilt command outputs are used wherever available. Remaining original
binaries and data are explicit base/ prerequisites in the Makefile; there
are no wildcard copies or dependencies on another project.

The tools disk carries HELP.CMD and the maintained HELP.HLP.

`cdos86.cfg` sets the PCE escape key to F12; PCE's default Esc prefix would
swallow Esc and turn the following key release into an emulator command.

`make check` (or `make check-media`) extracts every selected payload and
compares all source bytes, allowing only CP/M record padding. It also checks
327680-byte image sizes and all seven boot tracks. `make test` runs the same
PCE launcher/configuration convention as CCP/M, with system/tools on A:/B:.
The default adapter is VGA; `./cdos86 cga` selects CGA. `make check-pce` uses
disposable system/tools copies for the shell and keyboard regression.

From the project root, `make dist` copies the seven images to the root and
creates disks.zip with both license files and the project/command/patch notes.
`make check-dist` checks that disk archive. Source distribution stays in Git.
`make clean` removes generated media/releases, including the locally generated
base images; source and OEM inputs remain.
