INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86
INTEL_LINK86=intel_link86
INTEL_LOC86=intel_loc86
INTEL_OH86=intel_oh86
GENCMD=cpm86_gencmd
.PHONY: all clean
.DELETE_ON_ERROR:
all: pin.rsp
pin.rsp: pin.h86
	$(GENCMD) $< 'data[b1000]'
	mv pin.cmd $@
	cmdinfo $@
pin.loc: rhpin.obj pxios.obj pin.obj
	$(INTEL_LINK86) rhpin.obj, pxios.obj, pin.obj to pin.lnk
	$(INTEL_LOC86) pin.lnk 'od(sm(code,dats,data,stack,const))' 'ad(sm(code(0),dats(10000h)))' 'ss(stack(0))' to pin.loc
%.obj: %.a86
	$(INTEL_ASM86) $<
%.obj: %.plm $(wildcard *.lit)
	$(INTEL_PLM86) $< debug 'optimize(3)' xref
%.h86: %.loc
	$(INTEL_OH86) $<
	mv $*.hex $@
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.rsp *.cmd *.loc *.lnk *.mp?
