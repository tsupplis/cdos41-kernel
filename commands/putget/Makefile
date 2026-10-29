# PUTGET — ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd

TOOLS=put.cmd get.cmd rdr.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)

%.cmd: %.h86 Makefile
	$(GENCMD) $<
	cmdinfo $@

# Assemble absolute groups for GENCMD.
%.h86: %.a86 putget.def putget.lib Makefile
	$(ASM86) $<

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.cmd *.obj *.h86 *.sym *.lst *.prn *.loc *.lnk *.mp?

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in $(TOOLS); do cmdinfo $$f; done
