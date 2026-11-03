# TREE — native DR C and RASM86 build.
# all builds TREE.CMD; check validates it; clean removes generated outputs.
DRC86=drccpm_cc
RASM86=pcdev_rasm86
DRCLINK86=drccpm_link
CMDINFO=cmdinfo
TOOLS=tree.cmd
OBJECTS=tree.obj os.obj

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)
check: all
	$(CMDINFO) tree.cmd

tree.cmd: $(OBJECTS) Makefile
	@$(DRCLINK86) tree=tree,os > tree-link.log 2>&1; result=$$?; cat tree-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' tree-link.log
	$(CMDINFO) $@

%.obj: %.c Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]:])error([[:space:]:]|[0-9]|$$)|[1-9][0-9]* error\(s\) detected|fatal' $*.log
	@test -s $@
%.obj: %.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@
clean:
	$(RM) *.cmd *.obj *.h86 *.hex *.lst *.sym *.log *.lin *.prn *.mp? *.lnk *.map
