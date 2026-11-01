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

The top-level [command table](../README.md#commands) is the complete inventory
and defines the parity statuses. This work list uses those same statuses.
Provenance notes are kept below the table, separate from outstanding tasks.

Only Pending and Known gap entries are active work.

| Command/group | Parity | Remaining work |
| --- | --- | --- |
| CHDIR, MKDIR, SYSDISK, HDMAINT, REN.EXE, LOADCCPM, REDOS.COM, STOP.CMD | Byte-identical | None for release equivalence |
| SETPORT | Equivalent | None; 39 equivalent instruction encodings checked |
| INITDIR | Equivalent | None; overwritten runtime word checked |
| COPY.EXE, ERASE.EXE | Equivalent | None; exact serial/header/padding exceptions checked |
| RMDIR | Equivalent | None; copyright relocation checked, diagnostics aligned |
| SDIR | Behavior tested | No known fix pending; 27 option and 7 path/current-directory cases |
| WINDOW/WMENU | Behavior tested | No known fix pending; immediate colour repaint now checked against actual screen bytes |
| SHOW, SET, TYPE, TIME.EXE | Behavior tested | No known fix pending; retain documented regression coverage |
| SYSTAT | Behavior tested | Compared against the retained 4.1 original; no known fix pending |
| ERA, REN.CMD | Behavior tested | Import review complete against retained originals; release not established |
| SUBMIT | No reference | CCP/M-86 3.1 original unavailable. No active work. |
| DSKMAINT | Behavior tested | 512-byte loader matches 4.11. Format, cold boot and help navigation pass. See [DSKMAINT](dskmaint/README.md). |
| PATH.EXE | Equivalent | Complete-file check covers entry NOPs, skipped linker identification, unreachable group-copy operand and checksum. See [PATH](path/README.md). |
| ERAQ, PIP | Behavior tested | ERAQ confirmation, refusal and missing-file cases match. PIP verified copy, concatenation and missing source match. The interactive banner now identifies 4.1N. |
| CHSET | Behavior tested | Query and update match 4.11, including combined options, duplicate rejection and the resulting CMD bytes. Fixed the empty-field comparison. |
| COPYMENU, EDITMENU, DREDIX, FUNCTION, HELP | Behavior tested | Compared paired PCE screens for menu navigation, editor input, help and exit paths. See the release comparison target for cases. |
| DSP, PRINTMGR | Behavior tested | Compared startup and queue/error handling. PRINTMGR now uses the release default of 60 printed lines per 66-line form. Physical print output was not exercised. |
| BATCH | Equivalent | Restored the 4.11 console-attach order and priority reset. The OEM baseline with these changes differs only in four serial characters. Local prompt enhancements are retained. |
| DATE.EXE | Equivalent | Unmodified OEM command logic matches 4.11. The maintained short-year change passed 54 parser cases, and explicit-date entry/display were compared in PCE. |
| GENCCPM, GENLDR | No reference | No independent release binaries available |

SDIR's verified 4.11 reference is now `base/sdir.cmd`, replacing the older
CCP/M reference. Other original binaries were retained. SET matches one
of two variants in the 4.11 image set. Neither note by itself is an outstanding
code fix. Other imported/new tools without a retained CDOS release counterpart
are Additional tool, not implicitly pending replacements.

PATH.EXE, BATCH and DATE.EXE qualified for Equivalent in the review of 23
commands. PATH's complete file comparison accounts for the linker differences.
BATCH and DATE.EXE have verified 4.11 baselines and documented local improvements.

The other 20 commands retain Behavior tested. Their comparisons cover the
scenarios described in the table. Further differences in generated code,
startup, or rewritten command logic have not been fully accounted for.
