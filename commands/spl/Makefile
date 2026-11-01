# SPL - default DRC build, with a separately verified ASM86 reconstruction.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/spl.cmd
DRC86=drccpm_cc
RASM86=pcdev_rasm86
LINK86=drccpm_link
CMDINFO=cmdinfo

.PHONY: all check cbuild check-c check-asm check-live clean
.DELETE_ON_ERROR:

all: spl.cmd

spl.cmd: splc.cmd Makefile
	cp $< $@

splorg.h86: splorg.a86 Makefile
	@$(ASM86) $< > splorg.log 2>&1; result=$$?; cat splorg.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' splorg.log

splorg.cmd: splorg.h86 Makefile encodings.py
	$(GENCMD) $<
	$(PYTHON) encodings.py $@

check: all check-c check-asm
	cmp spl.cmd splc.cmd

check-asm: splorg.cmd
	cmp splorg.cmd $(REF)

cbuild: splc.cmd

splc.obj: splc.c splc.h Makefile
	@$(DRC86) -osplc.obj splc.c > splc.log 2>&1; result=$$?; cat splc.log; test $$result -eq 0
	@! grep -qiE 'error|unable to open|fatal' splc.log

# Reuse the surviving spooler family's assembly interfaces without changing them.
utlasm.obj: ../dsp/utlasm.a86 Makefile
	cp ../dsp/utlasm.a86 utlasm.a86
	@$(RASM86) utlasm.a86 > utlasm.log 2>&1; result=$$?; cat utlasm.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' utlasm.log
	$(RM) utlasm.a86

splc.cmd: splc.obj utlasm.obj Makefile
	@$(LINK86) 'splc,utlasm[data[max[140]]]' > splc-link.log 2>&1; result=$$?; cat splc-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' splc-link.log
	@test -s $@
	$(CMDINFO) $@

check-c: all
	$(PYTHON) tests/check.py

check-live: all
	$(PYTHON) tests/live.py

clean:
	$(RM) spl.cmd splorg.cmd splorg.h86 splorg.log splorg.lst splorg.sym
	$(RM) splc.cmd splc.obj splc.log splc-link.log splc.sym utlasm.obj utlasm.log utlasm.lst utlasm.sym
