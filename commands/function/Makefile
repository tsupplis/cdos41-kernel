ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=function.cmd
OBJECTS=func1.obj func2.obj func3.obj display.obj pccrt.obj system.obj screen.obj help1.obj help2.obj func10.obj

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

function.cmd: $(OBJECTS) Makefile
	@$(LINK86) 'function=func1[data[max[0]],locals,map[all]],func2,func3,display,pccrt,system,screen,help1,help2,func10' > function-link.log 2>&1; result=$$?; cat function-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' function-link.log
	@test -s $@
	cmdinfo $@

help1.obj: help1.a86
	$(INTEL_ASM86) $<
