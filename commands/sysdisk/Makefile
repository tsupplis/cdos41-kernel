ASM86=cpm86_asm86
GENCMD=cpm86_gencmd
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

%.obj: %.a86
	@$(RASM86) $< > $*.log 2>&1; result=$$?; cat $*.log; test $$result -eq 0
	@grep -qiE 'Number of errors: +0\.' $*.log

check: all
	cmdinfo $(TOOLS)

clean:
	rm -f *.obj *.h86 *.hex *.lst *.sym *.log *.cmd *.loc *.lnk *.mp? *.map
