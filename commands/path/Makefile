# PATH — RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.
# NPATH.LIB is shared with TMP/BATCH; PATHX.A86 remains the legacy DOS reference.
RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd
CMDINFO=cmdinfo
CMDMOD=cmdmod
TOOLS=path.cmd
OBJECTS=path.obj

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)

path.obj: path.a86 npath.lib pdata.lib Makefile
	@$(RASM86) $< > path.log 2>&1; result=$$?; cat path.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' path.log

path.cmd: $(OBJECTS) Makefile
	@$(LINK86) 'path=path[data[origin[0],max[0]]]' > path-link.log 2>&1; result=$$?; cat path-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' path-link.log
	@test -s $@
	$(CMDMOD) -f 1=1 $@
	$(CMDINFO) $@

# Validate native format, case-preserving tail and identical shared code.
check: all
	$(CMDINFO) path.cmd
	@python3 -c "from pathlib import Path; assert Path('path.cmd').read_bytes()[127]&2"
	cmp npath.lib ../../kernel/rsp3/npath.lib
	cmp npath.lib ../batch/npath.lib
	python3 ../../tools/path_unit_check.py

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) *.cmd *.obj *.h86 *.hex *.sym *.lst *.log *.lin *.prn *.lnk *.map *.mp? *.exe *.com
