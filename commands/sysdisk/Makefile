# SYSDISK — RASM86 build.
# all builds local outputs; check validates them; clean removes generated files.

RASM86=pcdev_rasm86
LINK86=pcdev_linkcmd

TOOLS=sysdisk.cmd
OBJECTS=sysdisk.obj path.obj derror.obj

.PHONY: all check clean
.DELETE_ON_ERROR:

all: $(TOOLS)

sysdisk.cmd: $(OBJECTS) Makefile
	@$(LINK86) 'sysdisk=sysdisk,path,derror' > sysdisk-link.log 2>&1; result=$$?; cat sysdisk-link.log; test $$result -eq 0
	@! grep -qiE 'undefined|unresolved|syntax error|unable|fatal' sysdisk-link.log
	@test -s $@
	cmdinfo $@

sysdisk.obj: sysdisk.a86 d.a86 Makefile
path.obj: path.a86 Makefile
derror.obj: derror.a86 Makefile

# Assemble relocatable objects; retain the module-specific linker layout.
%.obj: %.a86 Makefile $(wildcard *.lib *.equ *.def *.inc)
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

check: all
	cmdinfo $(TOOLS)

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.cmd *.loc *.lnk *.mp? *.map
