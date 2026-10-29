# HDMAINT — RASM86 / ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.
# Full build is pending: the 4.1 archive lacks flat LBDOS.H86.

ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd

TOOLS=hdmaint.cmd
OBJECTS=lbdos3.obj
IMAGES=pcboot1.h86 cpmboot2.h86 cpmboot3.h86 hsetup.h86 label.h86 pcboot2.h86 pcboot3.h86

.PHONY: all check clean components
.DELETE_ON_ERROR:

all: $(TOOLS)
check: all
	@set -e; for f in $(TOOLS); do cmdinfo $$f; done

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

# Assemble absolute groups for GENCMD.
%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

# The OEM HDMAINT recipe needs flat LBDOS.H86, which is not LBDOS3.A86.
# No older loader is substituted. Components can be inspected separately.
components: h70.cmd $(IMAGES) lbdos3.cmd

hdmaint.cmd:
	@echo 'HDMAINT pending: the 4.1 recipe requires missing flat LBDOS.H86.'
	@echo 'The supplied relocatable LBDOS3.A86 is not a replacement.'
	@exit 1

h70.cmd: h70.h86 Makefile
	$(GENCMD) $< 'data[m800]' 'extra[m800]'
	cmdinfo $@

lbdos3.cmd: lbdos3.obj Makefile
	@$(LINK86) 'lbdos3=lbdos3[data[ori[0],max[0]]]' > lbdos3-link.log 2>&1; result=$$?; cat lbdos3-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' lbdos3-link.log
	cmdinfo $@
