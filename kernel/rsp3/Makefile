# RSP3 — DR C / RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

.PHONY: all check clean
.DELETE_ON_ERROR:

all: pctmp.rsp confid.rsp
# Same installed cross-development tools as the CCP/M project.
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
# Included files are local copies; no sibling repository participates.
LOCAL_INCLUDES=$(wildcard *.def *.lib *.fmt *.cod *.sup *.rtm *.cio *.mem *.bdo *.dat *.equ *.mac *.h *.lit *.dcl)
# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 $(LOCAL_INCLUDES) Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
# Compile C modules with local declarations.
%.obj: %.c $(LOCAL_INCLUDES) Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -iE 'error|unable to open|fatal' $*.log
# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.con *.rsp *.cmd *.loc *.lnk *.mp? *.map

PCTMP=tmppc.obj dispmenu.obj runmenu.obj rmenuio.obj dmsubs.obj wwcall.obj ms1.obj ms2.obj
CONFID=rspdat.obj initrsp.obj nterface.obj
pctmp.rsp: $(PCTMP) pctmp.inp Makefile
	@$(DRCLINK86) 'pctmp[input]' > pctmp-link.log 2>&1; result=$$?; cat pctmp-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' pctmp-link.log
	$(CMDINFO) $@

confid.rsp: $(CONFID) confid.inp Makefile
	@$(LINK86) 'confid[input]' > confid-link.log 2>&1; result=$$?; cat confid-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' confid-link.log
	$(CMDINFO) $@

# Validate the structure of each rebuilt command/component.
check: all
	@set -e; for f in pctmp.rsp confid.rsp; do cmdinfo $$f; done
