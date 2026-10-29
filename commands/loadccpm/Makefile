ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
INTEL_PLM86=intel_plm86
INTEL_ASM86=intel_asm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link

TOOLS=loadccpm.com
OBJECTS=

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)
check: all
	@set -e; for f in $(TOOLS); do test -s $$f; done

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
	@grep -qiE '0 PROGRAM ERROR' $*.log

%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

clean:
	rm -f *.sys *.loc *.cmd *.obj *.h86 *.hex *.sym *.lin *.lst *.prn *.log
	rm -f *.mp? *.lnk *.map *.exe *.com

loadccpm.com: loadccpm.h86 Makefile
	$(GENCMD) $< nhead 8080 'code[b10]'
	mv loadccpm.cmd $@
	@python3 -c "from pathlib import Path; b=Path('$@').read_bytes(); assert b[0]==0xe9, 'Expected entry JMP at COM file offset zero'"
	@test -s $@

# LOADCCPM.SUB requests Intel HEX ($fi). GENCMD applies CODE[B10] to
# Intel address records; DRI type-81 records would retain a 256-byte gap.
loadccpm.h86: loadccpm.a86 Makefile
	@$(ASM86) $< '$$fi' > loadccpm.log 2>&1; result=$$?; cat loadccpm.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' loadccpm.log
