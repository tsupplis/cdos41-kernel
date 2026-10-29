ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=era.cmd eraq.cmd
OBJECTS=scd3.obj era.obj eraq.obj

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
	@grep -qiE '(^|[[:space:],])0 ERRORS' $*.log

%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

era.cmd: scd3.obj era.obj Makefile
	@$(LINK86) 'era=scd3,era[dat[ori[0]]]' > era-link.log 2>&1; result=$$?; cat era-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' era-link.log
	@test -s $@
	cmdinfo $@

eraq.cmd: scd3.obj eraq.obj Makefile
	@$(LINK86) 'eraq=scd3,eraq[dat[ori[0]]]' > eraq-link.log 2>&1; result=$$?; cat eraq-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' eraq-link.log
	@test -s $@
	cmdinfo $@
