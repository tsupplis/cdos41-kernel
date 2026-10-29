# !!!WIP!!! Concurrent DOS 4.1 kernel and commands

Independent source rebuild of the OEM Concurrent DOS 4.1 distribution.
The layout follows the CCP/M kernel project: `kernel/con`, `kernel/rsp1`,
`kernel/rsp2`, `kernel/rsp3`, `kernel/sysgen`, and one directory per command.
No build rule reads another project or the historical source archive.

## Build

```sh
make                 # kernel components and the 27 enabled command families
make check           # builds, headers, GENCMD self-host and DSKMAINT embedding checks
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

Historical source bytes are preserved, including DOS line endings and EOF
padding. Makefiles check assembler/compiler/linker diagnostics because some
historical tools return success after an error. Included local sources are
normal prerequisites. The PIP source and Makefile were copied unchanged from
the ready 4.1-mode build; it produces `pip4.cmd` (and retains `pip3.cmd`).
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
System-generation configuration, boot media and boot validation are the next
integration step; the 3.1 GENCCPM response file is not compatible unchanged
with the 4.1 disk-buffer prompts. No placeholder `ccpm.sys` is shipped.

## Enabled command builds

The top-level build now includes these 27 command families:

- Development and system generation: ASM86, GENCMD, SUBMIT, GENCCPM, GENLDR.
- File and disk utilities: PIP (pip3/pip4), BATCH, CHDIR, MKDIR, RMDIR,
  SYSDISK, CHSET, INITDIR, ERAQ, HELP, FUNCTION and DSKMAINT.
- Editor and menus: DREDIX, COPYMENU and EDITMENU.
- Printing: PRINTMGR and DSP.
- DOS outputs: LOADCCPM.COM, COPY.EXE, DATE.EXE, ERASE.EXE and PATH.EXE.

RMDIR and SYSDISK select the original ZD and SD modes of `D.A86`, using
small new wrappers patterned on CHDIR/MKDIR. D.A86 is a shared module,
not a standalone command. Historical 4.1 program sources remain unchanged.

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
  substituted. Its components can be built separately for investigation.
- REDOS implementation source is missing.
- HELP.CMD builds, but the 4.1 HELP.DAT text is absent, so HELP.HLP is not
  generated. Menu utilities' serial-terminal mode needs separate TERM data.

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
