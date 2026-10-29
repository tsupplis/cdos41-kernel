TOOLS=
SNIPPETS=ccpm.sys
CONS=bdos.con cio.con mem.con rtm.con sup.con sysdat.con xios.con
RSPS=pin.rsp clock.rsp pctmp.rsp confid.rsp
GENCCPM=$(abspath ../../commands/genccpm/genccpm.cmd)

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS) $(SNIPPETS)

$(CONS): %.con: ../con/%.con
	cp $< $@
pin.rsp: ../rsp1/pin.rsp
	cp $< $@
clock.rsp: ../rsp2/clock.rsp
	cp $< $@
pctmp.rsp: ../rsp3/pctmp.rsp
	cp $< $@
confid.rsp: ../rsp3/confid.rsp
	cp $< $@

# GENCCPM enumerates every local *.RSP. Use a fresh, isolated selection.
ccpm.sys: ../../commands/genccpm/genccpm.cmd genccpm.in Makefile $(CONS) $(RSPS)
	@tmp=$$(mktemp -d ./sysgen.XXXXXX); \
	trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	cp $(CONS) $(RSPS) "$$tmp/"; \
	(cd "$$tmp" && emu2 "$(GENCCPM)" < ../genccpm.in) > sysgen.log 2>&1 && \
	test -s "$$tmp/ccpm.sys" && cp "$$tmp/ccpm.sys" $@.tmp && \
	cmdinfo $@.tmp && mv $@.tmp $@

check: ccpm.sys
	cmdinfo $<
	@python3 -c "from pathlib import Path; b=Path('$<').read_bytes(); c=int.from_bytes(b[1:3],'little'); d=int.from_bytes(b[10:12],'little'); base=int.from_bytes(b[3:5],'little'); assert b[0]==1 and b[9]==2 and base==0x6000; assert b[12:14]==(base+c).to_bytes(2,'little'); assert len(b)>=128+(c+d)*16; s=b[128+c*16:]; assert int.from_bytes(s[0x40:0x42],'little')==base; assert int.from_bytes(s[0x44:0x46],'little')<=0xa000"

clean:
	$(RM) $(CONS) $(RSPS) *.sys *.old *.tmp *.log
