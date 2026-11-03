# SYSGEN — standard and optional FIDD system images from the same components.
# GENCCPM response files select RSP inclusion; media uses ccpm.sys.

TOOLS=ccpm.sys ccpmfidd.sys
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

ccpm.sys: RESPONSE=genccpm.in
ccpm.sys: CONFID=0
ccpm.sys: LOG=sysgen.log
ccpm.sys: genccpm.in

ccpmfidd.sys: RESPONSE=genfidd.in
ccpmfidd.sys: CONFID=1
ccpmfidd.sys: LOG=sysgen-fidd.log
ccpmfidd.sys: genfidd.in

# Stage only declared components. Each output has an isolated GENCCPM run:
# no stale RSP can leak in, and parallel builds cannot overwrite each other.
$(TOOLS): ../../commands/genccpm/genccpm.cmd Makefile ../../tools/sysgen_check.py $(CONS) $(RSPS)
	@tmp=$$(mktemp -d ./sysgen.XXXXXX); \
	trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	cp $(CONS) $(RSPS) "$$tmp/"; \
	(cd "$$tmp" && emu2 "$(GENCCPM)" < "$(abspath $(RESPONSE))") > $(LOG) 2>&1 && \
	test -s "$$tmp/ccpm.sys" && \
	python3 ../../tools/sysgen_check.py "$$tmp/ccpm.sys" --confid $(CONFID) && \
	cp "$$tmp/ccpm.sys" $@.tmp && \
	cmdinfo $@.tmp && mv $@.tmp $@

check: $(TOOLS)
	python3 ../../tools/sysgen_check.py ccpm.sys --confid 0
	python3 ../../tools/sysgen_check.py ccpmfidd.sys --confid 1
	python3 ../../tools/sysgen_profiles_check.py

# Remove generated outputs only; preserve sources and response files.
clean:
	$(RM) $(CONS) $(RSPS) .confid-0 .confid-1 *.sys *.old *.tmp *.log
