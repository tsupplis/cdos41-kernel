# Concurrent DOS 4.1 media

Seven physical-CHS 320 KB images are built locally. The layout follows the
CCP/M media workflow: generated base.img, source-built boot track in
cdos86base.img, then untwist / populate / twist for each distribution disk.
All disks include the rebuilt PIP4 as PIP.CMD. Only the system and maintenance
disks contain CCPM.SYS and STARTUP.0; the remaining disks are data-only.

| Image | Bootable | Contents |
| --- | --- | --- |
| cdos86.img | Yes | Kernel, native file commands/editor, DATE, SDIR, SET, SHOW, SUBMIT, BATCH, SYSDISK, ERA/ERAQ; OEM REN.EXE and STOP.CMD for shell aliases. |
| cdostools.img | No | ASM80/ASM86, GENCMD, GENCCPM, HEXCOM, HELP/HLP, PRINT, SYSTAT, CHSET, GENLDR, LOADCCPM, WINDOW/WMENU and core commands. |
| cdosmaint.img | Yes | Kernel, DSKMAINT, DCOPY, DCOMP, INITDIR and core commands. |
| cdosmenu.img | No | DREDIX, COPYMENU, EDITMENU, PRINTMGR, DSP, menu/terminal/message data, window BAT examples and sample text. |
| cdosdos.img | No | Rebuilt COPY.EXE, DATE.EXE, ERASE.EXE, PATH.EXE; original TIME.EXE, REN.EXE and REDOS.COM; core commands. |
| cdosoem1.img | No | Original BACK, REST, BRINST, FM, SPL and backup/file-manager support files. |
| cdosoem2.img | No | Rebuilt FUNCTION and HELP; original SETUP, SETPORT, DISKSTAT, FIND, N, NS, SID86, STAT, STOP, HDMAINT, its manual and the original 4.1 HELP.HLP. |

Rebuilt command outputs are used wherever available. Remaining original
binaries and data are explicit base/ prerequisites in the Makefile; there
are no wildcard copies or dependencies on another project. HDMAINT's source
build remains pending the missing LBDOS loader: its unmodified OEM binary
is preserved on cdosoem2.img. REDOS's source is still missing; its original
COM is on cdosdos.img. TIME.EXE likewise awaits the later datetime source work.

The tools disk uses HELP.HLP rebuilt from the imported CCP/M HELP.DAT baseline.
The second OEM disk pairs rebuilt HELP.CMD with original 4.1 HELP.HLP for the
historical documentation. Use B:HELP after inserting the desired disk in B:.
Alignment of imported command behavior/help text against the OEM release is
still a separate review; packaging does not assert binary identity.

`make check` (or `make check-media`) extracts every selected payload and
compares all source bytes, allowing only CP/M record padding. It also checks
327680-byte image sizes and all seven boot tracks. `make test` runs the same
PCE launcher/configuration convention as CCP/M, with system/tools on A:/B:.
The default adapter is VGA; `./cdos86 cga` selects CGA. `make check-pce` uses
disposable system/tools copies for the shell and keyboard regression.

From the project root, `make dist` copies the seven images to the root,
creates disks.zip with the license files and project/command/patch notes,
and writes dist/cdos86-source.tar.gz plus dist/source-files.txt.
`make source-dist` creates the source archive independently. `make check-dist`
checks both archive containers. `make clean` removes generated media/releases,
including the locally generated base images; source and OEM inputs remain.
