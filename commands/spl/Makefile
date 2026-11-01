# SPL — local command build.
# all builds the declared tools; check validates them; clean removes generated files.
.PHONY: all check cbuild check-c check-asm check-live clean

CMDINFO=cmdinfo
RASM86=pcdev_rasm86
DRC86=drccpm_cc
DRCLINK86=drccpm_link
RM=rm -f
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
PYTHON=python3
REF=../../base/spl.cmd

TOOLS=spl.cmd

all: $(TOOLS)

spl.cmd: splc.cmd Makefile
	cp $< $@

splorg.cmd: splorg.h86 Makefile encodings.py
	$(GENCMD) $<
	$(PYTHON) encodings.py $@

cbuild: splc.cmd

splc.cmd: splc.obj utlasm.obj Makefile
	$(DRCLINK86) 'splc,utlasm[data[max[140]]]'
	$(CMDINFO) $@

splorg.h86: splorg.a86 Makefile
	$(ASM86) $<

# Reuse the surviving spooler family's assembly interfaces without changing them.
utlasm.obj: ../dsp/utlasm.a86 Makefile
	cp ../dsp/utlasm.a86 utlasm.a86
	$(RASM86) utlasm.a86
	$(RM) utlasm.a86

%.obj: %.c Makefile $(wildcard *.h)
	$(DRC86) -o$@ $<

clean:
	$(RM) *.sys *.loc *.cmd *.obj *.h86 *.sym *.lin *.lst *.prn ccpmtest.img *.log
	$(RM) *.loc *.mp? *.lnk *.map
	$(RM) utlasm.a86

# Structural validation; byte comparisons or runtime checks are separate where available.
check: all check-c check-asm
	@set -e; for file in $(TOOLS); do $(CMDINFO) $$file; done
	cmp spl.cmd splc.cmd

check-asm: splorg.cmd
	cmp splorg.cmd $(REF)

check-c: all
	$(PYTHON) tests/check.py

check-live: all
	$(PYTHON) tests/live.py
