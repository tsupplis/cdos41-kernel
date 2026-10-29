all: sup.con rtm.con cio.con mem.con sysdat.con bdos.con xios.con
# Same installed cross-development tools as the CCP/M project.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
.DELETE_ON_ERROR:
# Included files are local copies; no sibling repository participates.
LOCAL_INCLUDES=$(wildcard *.def *.lib *.fmt *.cod *.sup *.rtm *.cio *.mem *.bdo *.dat *.equ *.mac *.h *.lit *.dcl)
%.h86: %.a86 $(LOCAL_INCLUDES)
	@$(ASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' $*.log
%.obj: %.a86 $(LOCAL_INCLUDES)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
%.obj: %.c $(LOCAL_INCLUDES)
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -iE 'error|unable to open|fatal' $*.log
%.con: %.h86
	$(GENCMD) $<
	mv $*.cmd $@
	$(CMDINFO) $@
%.rsp: %.h86
	$(GENCMD) $<
	mv $*.cmd $@
	$(CMDINFO) $@
%.cmd: %.h86
	$(GENCMD) $<
	$(CMDINFO) $@
.PHONY: clean
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.con *.rsp *.cmd *.loc *.lnk *.mp? *.map
bdos.con: pcbdos.obj black.obj
	@$(LINK86) 'bdos.con=pcbdos,black[data[origin[0]]]' > bdos-link.log 2>&1; result=$$?; cat bdos-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' bdos-link.log
	$(CMDINFO) $@
xios.con: squid.h86
	$(GENCMD) $< 8080
	mv squid.cmd $@
	$(CMDINFO) $@
.PHONY: all
