ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=hdmaint.cmd
OBJECTS=lbdos3.obj
IMAGES=pcboot1.h86 cpmboot2.h86 cpmboot3.h86 hsetup.h86 label.h86 pcboot2.h86 pcboot3.h86

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)
check: all
	@set -e; for f in $(TOOLS); do cmdinfo $$f; done

LOCAL_INCLUDES=$(wildcard *.a86 *.lib *.equ *.dat *.def *.h *.dcl)
$(OBJECTS): $(LOCAL_INCLUDES) Makefile

%.obj: %.a86
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

%.obj: %.c
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE 'error|unable to open|fatal' $*.log

%.obj: %.plm
	@$(INTEL_PLM86) $< debug 'optimize(3)' xref > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE '0 ERRORS' $*.log

%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

# The OEM HDMAINT recipe needs flat LBDOS.H86, which is not LBDOS3.A86.
# No older loader is substituted. Components can be inspected separately.
.PHONY: components
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
