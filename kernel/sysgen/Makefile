# SYSGEN — local component build.
# all builds local outputs; check validates them; clean removes generated files.

TOOLS=ccpm.sys
CONS=bdos.con cio.con mem.con rtm.con sup.con sysdat.con xios.con
RSPS=pin.rsp clock.rsp pctmp.rsp confid.rsp
GENCCPM=$(abspath ../../commands/genccpm/genccpm.cmd)

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)

$(CONS): %.con: ../con/%.con
	cp $< $@

pin.rsp: ../rsp1/pin.rsp Makefile
	cp $< $@

clock.rsp: ../rsp2/clock.rsp Makefile
	cp $< $@

pctmp.rsp: ../rsp3/pctmp.rsp Makefile
	cp $< $@

confid.rsp: ../rsp3/confid.rsp Makefile
	cp $< $@

# GENCCPM enumerates every local *.RSP. Use a fresh, isolated selection.
ccpm.sys: ../../commands/genccpm/genccpm.cmd genccpm.in Makefile ../../tools/sysgen_check.py $(CONS) $(RSPS)
	@tmp=$$(mktemp -d ./sysgen.XXXXXX); \
	trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	cp $(CONS) $(RSPS) "$$tmp/"; \
	(cd "$$tmp" && emu2 "$(GENCCPM)" < ../genccpm.in) > sysgen.log 2>&1 && \
	test -s "$$tmp/ccpm.sys" && \
	python3 ../../tools/sysgen_check.py "$$tmp/ccpm.sys" && \
	cp "$$tmp/ccpm.sys" $@.tmp && \
	cmdinfo $@.tmp && mv $@.tmp $@

check: ccpm.sys
	cmdinfo $<
	python3 ../../tools/sysgen_check.py $<

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) $(CONS) $(RSPS) *.sys *.old *.tmp *.log
