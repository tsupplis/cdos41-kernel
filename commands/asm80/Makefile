# ASM80 — ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: asm80.cmd

asm80.cmd: asm80.h86 Makefile
	$(GENCMD) $< 8080 'code[xfff]'

# Assemble absolute groups for GENCMD.
%.h86: %.a86 Makefile $(wildcard *.lib *.def *.equ *.inc)
	$(ASM86) $<
	[ -f $@ ]

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) *.prn *.lst *.h86 *.cmd

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in asm80.cmd; do cmdinfo $$f; done
