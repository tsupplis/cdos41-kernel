# GENCCPM — CDOS 4.1 C-source system generator.
# all builds GENCCPM.CMD; kernel/sysgen invokes it to compose CCPM.SYS.

DRC86=drccpm_cc
DRCLINK86=drccpm_link
CMDINFO=cmdinfo

TOOLS=genccpm.cmd
OBJECTS=genc1.obj genc2.obj genc3.obj genc4.obj genc5.obj genc6.obj
HEADERS=$(wildcard *.h)

.PHONY: all check clean
.DELETE_ON_ERROR:
all: $(TOOLS)

# Preserve the original C module order and runtime supplied by the C linker.
genccpm.cmd: $(OBJECTS) Makefile
	@$(DRCLINK86) 'genccpm=genc1,genc2,genc3,genc4,genc5,genc6' > genccpm-link.log 2>&1; result=$$?; cat genccpm-link.log; test $$result -eq 0
	@! grep -iE 'undefined|syntax error|unable' genccpm-link.log
	$(CMDINFO) $@

%.obj: %.c $(HEADERS) Makefile
	@$(DRC86) -o$@ $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@! grep -iE 'error|unable to open|fatal' $*.log

# Validate the rebuilt command structure; system-image checks live in sysgen.
check: all
	$(CMDINFO) $(TOOLS)

# Remove generated command, objects, listings and linker outputs.
clean:
	$(RM) *.cmd *.obj *.lst *.sym *.map *.log
