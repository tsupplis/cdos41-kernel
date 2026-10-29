# SUBMIT — ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd

TOOLS=submit.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)

submit.cmd: submit.h86 Makefile
	$(GENCMD) $<
	cmdinfo $@

# Assemble absolute groups for GENCMD.
%.h86: %.a86 Makefile $(wildcard *.lib *.def *.equ *.inc)
	$(ASM86) $<

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn
	rm -f *.loc *.mp? *.lnk

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in $(TOOLS); do cmdinfo $$f; done
