# ECHO — native RASM86/LINKCMD build.
# all builds ECHO.CMD; check validates it; clean removes outputs.
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
CMDINFO=cmdinfo
CMDMOD=cmdmod
TOOLS=echo.cmd
OBJECTS=echo.obj

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)
check: all
	$(CMDINFO) echo.cmd
	@python3 -c "from pathlib import Path; assert Path('echo.cmd').read_bytes()[127] & 2, 'Expected CMD TAIL=KEEP flag'"

echo.cmd: $(OBJECTS) Makefile
	@$(LINK86) 'echo=echo[data[origin[0],max[0]]]' > echo-link.log 2>&1; result=$$?; cat echo-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' echo-link.log
	@test -s $@
	$(CMDMOD) -f 1=1 $@
	$(CMDINFO) $@
%.obj: %.a86 Makefile
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log
	@test -s $@
clean:
	$(RM) *.cmd *.exe *.obj *.h86 *.hex *.lst *.sym *.log *.lin *.prn *.mp? *.lnk *.map
