# Command builds

Each enabled command has a self-contained Makefile using the same conventions
as the CCP/M project. No build reads files from a sibling project.

- `make` / `make all` builds the local outputs.
- `make check` builds first and validates them; documented behavioral or
  reconstruction checks are included where available.
- `make clean` removes generated outputs, preserving source and references.

`make -C commands check` runs every enabled command's check and validates the
aggregate CMD, EXE and COM outputs. HDMAINT is excluded while its required flat
LBDOS loader remains missing; its `components` target remains available.

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
