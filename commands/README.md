# Command builds

Each enabled command has a self-contained Makefile using the same conventions
as the CCP/M project. No build reads files from a sibling project.

- `make` / `make all` builds the local outputs.
- `make check` builds first and validates them; documented behavioral or
  reconstruction checks are included where available.
- `make clean` removes generated outputs, preserving source and references.

`make -C commands check` runs every enabled command's check and validates the
aggregate CMD, EXE and COM outputs. HDMAINT is enabled; its recovered flat LBDOS and loader bundle are checked
against the original command.

Makefiles declare only the tools and recipes used locally. Source compilation
uses `$<`; declarations, included files, linker control files and Makefiles are
prerequisites where needed. Link order, memory sizing and format-specific
header handling remain local and documented. `.PHONY` and `.DELETE_ON_ERROR`
keep administrative targets reliable and remove failed outputs. Compiler logs
are checked where the historical tools do not reliably report failure.

Reconstructed commands keep a frozen original source and explicit comparison
rules. SETPORT's README lists its 39 equivalent ASM86 encoding exceptions;
its check permits no other byte differences. PRINT and WINDOW use wildcard
object cleanup like the other tools.

## Reference Makefiles

SYSTAT, PIP, SUBMIT, REN, ED, ASM86, DDT86, ASM80, HEXCOM, GENCMD and
DISK are the reference models for the corresponding toolchains. Their
Makefiles are excluded from this CDOS cleanup; alignment across the CP/M,
CCP/M and CDOS projects is a separate pass. The other command Makefiles
follow their all/check/clean, declared-tool and local-prerequisite conventions
without changing linker order or memory sizing.

DDT86 is built locally from Concurrent CP/M-86 3.1 sources and distributed
as DDT86.CMD on cdostools.img alongside ASM86. GENTAB.CMD is a build helper,
not a separate development-disk payload.

## 4.11 reference assessment

Use the independent `cdos-4.11-*.img` release as the reference from now on.
`../base/cdos411.json` records image hashes, extracted filenames, file hashes,
and whether an existing base binary was retained. Missing binaries have been
restored locally; no build depends on the external archive. Reference imports
do not add tools to the distribution. CARDFILE, LOAD6300 and COMPAQ are retained
as references only. Supplemental image contents also remain references only.

"Rebuild" below means the maintained build, including local patches, not a
fresh pristine-OEM compilation. A binary difference alone is not a defect.

| Command/group | Current assessment against 4.11 | Next step |
| --- | --- | --- |
| CHDIR, MKDIR, SYSDISK, HDMAINT, REN.EXE | Byte-identical | Closed |
| SETPORT | Only 39 documented equivalent instruction encodings | Closed; existing check |
| INITDIR | Only an overwritten runtime stack-limit word differs | Closed; new complete-file check and tool README |
| COPY.EXE | Path guard aligned; only serial and exact MZ header differences remain | Closed; complete-file check and 18 routine cases |
| RMDIR | Main/PATH logic matches; three diagnostic improvements in 4.11 | Assessed; diagnostic port pending, see tool README |
| LOADCCPM, DSKMAINT | Binary differences not yet classified | Next priority |
| PATH.EXE, ERASE.EXE, FUNCTION, ERAQ | Binary differences not yet classified | Pending |
| CHSET, DREDIX, COPYMENU, EDITMENU, PRINTMGR, DSP | Compiler/runtime versus logic differences not yet separated | Pending |
| BATCH, PIP, HELP, DATE.EXE | Intentional local changes exist; residual differences not yet classified | Pending |
| TIME.EXE | Reconstruction and formatting correction already tested | Retain regression coverage |
| WINDOW/WMENU, SHOW, SET, TYPE | Existing parity review used a reference matching 4.11 | Retain coverage; SET has two image variants |
| SDIR | 27 paired cases against 4.11; no new legacy-option gap found | Assessed; retain directory/date/SHORT/HELP improvements; path coverage pending |
| GENCCPM, GENLDR | No original in this release-image set | Separate reference needed |

Existing base files were not overwritten. SDIR uses `base/sdir411.cmd` as
its independent 4.11 oracle; the older `base/sdir.cmd` is retained separately. SET's two image variants are both recorded in the
manifest; the current base matches one. Other retained imports without a 4.11
counterpart are not newly certified by this audit.
