# RSP1 — Intel PL/M-86 / Intel ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86
INTEL_LINK86=intel_link86
INTEL_LOC86=intel_loc86
INTEL_OH86=intel_oh86
GENCMD=cpm86_gencmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: pin.rsp
pin.rsp: pin.h86 Makefile
	$(GENCMD) $< 'data[b1000]'
	mv pin.cmd $@
	cmdinfo $@

pin.loc: rhpin.obj pxios.obj pin.obj Makefile
	$(INTEL_LINK86) rhpin.obj, pxios.obj, pin.obj to pin.lnk
	$(INTEL_LOC86) pin.lnk 'od(sm(code,dats,data,stack,const))' 'ad(sm(code(0),dats(10000h)))' 'ss(stack(0))' to pin.loc
# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	$(INTEL_ASM86) $<
# Compile PL/M sources; declarations and Makefile changes trigger recompilation.
%.obj: %.plm $(wildcard *.lit) Makefile
	$(INTEL_PLM86) $< debug 'optimize(3)' xref
# Convert the located Intel object to H86.
%.h86: %.loc Makefile
	$(INTEL_OH86) $<
	mv $*.hex $@
# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.rsp *.cmd *.loc *.lnk *.mp?

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in pin.rsp; do cmdinfo $$f; done
