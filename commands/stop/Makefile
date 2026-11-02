# STOP - assemble the labelled 8086 source and restore the release encodings.
ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
INTEL_ASM86=intel_asm86
INTEL_PLM86=intel_plm86
INTEL_LINK86=intel_link86
INTEL_LOC86=intel_loc86
INTEL_OH86=intel_oh86
PYTHON=python3
REF=../../base/stop.cmd

.PHONY: all check check-plm clean
.DELETE_ON_ERROR:

all: stop.cmd

stop.h86: stop.a86 Makefile
	@$(ASM86) $< > stop.log 2>&1; result=$$?; cat stop.log; test $$result -eq 0
	@grep -qiE 'NUMBER OF ERRORS: +0' stop.log
	@test -s $@

stop.cmd: stop.h86 Makefile encodings.py
	$(GENCMD) $<
	$(PYTHON) encodings.py
	@test -s $@

scd86.obj: ../systat/scd.a86 Makefile
	@EMU2_DRIVE_E="$(abspath ../systat)" $(INTEL_ASM86) 'E:\SCD.A86' \
	  'object(scd86.obj)' 'print(scd86.lst)' > scd86.log 2>&1; \
	  result=$$?; cat scd86.log; test $$result -eq 0
	@grep -qi 'ASSEMBLY COMPLETE, NO ERRORS FOUND' scd86.log
	@test -s $@

stop_plm.obj: stop_plm.plm Makefile
	@$(INTEL_PLM86) $< debug 'optimize(3)' xref > stop_plm.log 2>&1; \
	  result=$$?; cat stop_plm.log; test $$result -eq 0
	@grep -qiE 'COMPILATION COMPLETE[.[:space:]]+[0-9]+ WARNINGS,[[:space:]]+0 ERRORS' stop_plm.log
	@test -s $@

stop_plm.lnk: scd86.obj stop_plm.obj Makefile
	@$(INTEL_LINK86) scd86.obj, stop_plm.obj to $@ > stop_plm-link.log 2>&1; \
	  result=$$?; cat stop_plm-link.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]])(ERROR[[:space:]]+[0-9]|FATAL)' stop_plm-link.log
	@test -s $@

stop_plm.loc: stop_plm.lnk Makefile
	@$(INTEL_LOC86) $< 'od(sm(code,dats,data,stack,const))' \
	  'ad(sm(code(0),dats(10000h)))' 'ss(stack(+200h))' to $@ > stop_plm-loc.log 2>&1; \
	  result=$$?; cat stop_plm-loc.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]])(ERROR[[:space:]]+[0-9]|FATAL)' stop_plm-loc.log
	@test -s $@ && test -s stop_plm.mp2

stop_plm.h86: stop_plm.loc Makefile
	@$(INTEL_OH86) $< > stop_plm-oh.log 2>&1; \
	  result=$$?; cat stop_plm-oh.log; test $$result -eq 0
	@grep -qi 'CONVERSION COMPLETE, NO ERRORS' stop_plm-oh.log
	@test -s stop_plm.hex
	mv stop_plm.hex $@

PARA = sub(/H$$/,"",s); sub(/.$$/,"",s); sub(/^0+/,"",s); print tolower(s); exit
GENCMD_BASE = $(shell awk '/DATS +DATA/{s=$$1; $(PARA)}' stop_plm.mp2)
GENCMD_MEM = $(shell awk '/MEMORY +MEMORY/{s=$$1; $(PARA)}' stop_plm.mp2)
GENCMD_MIN = $(shell printf '%x' $$((0x$(GENCMD_MEM)-0x$(GENCMD_BASE))))

stop_plm.cmd: stop_plm.h86 stop_plm.loc Makefile
	@test -n "$(GENCMD_BASE)" -a -n "$(GENCMD_MEM)" || \
	  { echo "stop: cannot derive DATS/MEMORY from stop_plm.mp2" >&2; exit 1; }
	@$(GENCMD) $< 'data[b$(GENCMD_BASE) m$(GENCMD_MIN) xfff]' > stop_plm-gencmd.log 2>&1; \
	  result=$$?; cat stop_plm-gencmd.log; test $$result -eq 0
	@! grep -qiE '(^|[[:space:]])(ERROR|FATAL|INVALID)' stop_plm-gencmd.log
	@grep -qiE 'RECORDS WRITTEN[[:space:]]+[1-9][0-9]*' stop_plm-gencmd.log
	@test -s $@

check: all check-plm $(REF)
	cmp stop.cmd $(REF)

check-plm: stop_plm.cmd tests/stopcheck.asm tests/stop_check.py $(REF)
	$(PYTHON) tests/stop_check.py $(REF) stop_plm.cmd

clean:
	$(RM) stop.cmd stop.h86 stop.log stop.lst stop.sym
	$(RM) scd86.obj scd86.lst scd86.log
	$(RM) stop_plm.cmd stop_plm.obj stop_plm.lnk stop_plm.loc stop_plm.hex stop_plm.h86
	$(RM) stop_plm.lst stop_plm.mp? stop_plm.log stop_plm-link.log stop_plm-loc.log
	$(RM) stop_plm-oh.log stop_plm-gencmd.log
