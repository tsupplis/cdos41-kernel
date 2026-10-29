# RSP2 — ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

.PHONY: all check clean
.DELETE_ON_ERROR:

all: clock.rsp
# Same installed cross-development tools as the CCP/M project.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
CMDINFO=cmdinfo
# Included files are local copies; no sibling repository participates.
LOCAL_INCLUDES=$(wildcard *.def *.lib *.fmt *.cod *.sup *.rtm *.cio *.mem *.bdo *.dat *.equ *.mac *.h *.lit *.dcl)
# Assemble absolute groups for GENCMD.
%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log

%.rsp: %.h86 Makefile
	$(GENCMD) $<
	mv $*.cmd $@
	$(CMDINFO) $@
# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.con *.rsp *.cmd *.loc *.lnk *.mp? *.map

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in clock.rsp; do cmdinfo $$f; done
