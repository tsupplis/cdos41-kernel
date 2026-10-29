# CON — RASM86 / ASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

.PHONY: clean all check-cursor check-rtc check
.DELETE_ON_ERROR:

all: sup.con rtm.con cio.con mem.con sysdat.con bdos.con xios.con
# Same installed cross-development tools as the CCP/M project.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
CMDINFO=cmdinfo
# Included files are local copies; no sibling repository participates.
LOCAL_INCLUDES=$(wildcard *.def *.lib *.fmt *.cod *.sup *.rtm *.cio *.mem *.bdo *.dat *.equ *.mac *.h *.lit *.dcl)
# Assemble absolute groups for GENCMD.
%.h86: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log
# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

%.con: %.h86 Makefile
	$(GENCMD) $<
	mv $*.cmd $@
	$(CMDINFO) $@
# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.con *.rsp *.cmd *.loc *.lnk *.mp? *.map

bdos.con: pcbdos.obj black.obj Makefile
	@$(LINK86) 'bdos.con=pcbdos,black[data[origin[0]]]' > bdos-link.log 2>&1; result=$$?; cat bdos-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' bdos-link.log
	$(CMDINFO) $@

xios.con: squid.h86 Makefile
	$(GENCMD) $< 8080
	mv squid.cmd $@
	$(CMDINFO) $@

check-cursor: xios.con squid.h86
	python3 ../../tools/cursor_check.py

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in sup.con rtm.con cio.con mem.con sysdat.con bdos.con xios.con; do cmdinfo $$f; done

# Exercise actual assembled RTC code with synthetic INT 1Ah services.
check-rtc: xios.con squid.h86
	python3 ../../tools/rtc_check.py
