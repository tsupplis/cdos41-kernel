# XIOS — RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

.PHONY: all check clean
.DELETE_ON_ERROR:

all: cpxios.con
# Same installed cross-development tools as the CCP/M project.
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
CMDINFO=cmdinfo
# Included files are local copies; no sibling repository participates.
LOCAL_INCLUDES=$(wildcard *.def *.lib *.fmt *.cod *.sup *.rtm *.cio *.mem *.bdo *.dat *.equ *.mac *.h *.lit *.dcl)
# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.con *.rsp *.cmd *.loc *.lnk *.mp? *.map

OBJECTS=headentr.obj intvec.obj pic.obj np8087.obj ctc.obj tick.obj conout.obj serout.obj auxio.obj vscreen.obj conin.obj serin.obj ssint.obj i3int.obj servar.obj pcmode.obj statline.obj list.obj switch.obj vccb.obj serdata.obj dentry.obj reskew.obj mdisk.obj dpbs.obj fdsel.obj fdrw.obj fdfmt.obj hdisk.obj
cpxios.con: $(OBJECTS) cpxios.inp Makefile
	@$(LINK86) 'cpxios[input]' > cpxios-link.log 2>&1; result=$$?; cat cpxios-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' cpxios-link.log
	$(CMDINFO) $@

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in cpxios.con; do cmdinfo $$f; done
