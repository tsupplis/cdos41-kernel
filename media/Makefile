PYTHON ?= python3
FORMAT=ccpm86-320
TWIST=$(PYTHON) ../tools/cpm86twist.py
CPMCP=cpmcp -f $(FORMAT)
IMAGES=cdos86.img cdostools.img
SYSTEM_COMMANDS=../commands/batch/batch.cmd ../commands/sysdisk/sysdisk.cmd
TOOLS_COMMANDS=../commands/asm86/asm86.cmd ../commands/gencmd/gencmd.cmd \
    ../commands/submit/submit.cmd ../commands/genccpm/genccpm.cmd \
    ../commands/batch/batch.cmd ../commands/sysdisk/sysdisk.cmd
PIP=../commands/pip/pip4.cmd

.PHONY: all check check-pce test clean
.DELETE_ON_ERROR:
all: $(IMAGES)

# Generate the empty physical-CHS filesystem template locally.
# The rest follows the CCP/M media pattern: install boot, untwist, populate,
# then twist the completed distribution image back to physical CHS order.
base.img: diskdefs Makefile
	mkfs.cpm -f $(FORMAT) $@.logical.tmp
	$(PYTHON) -c "from pathlib import Path; p=Path('$@.logical.tmp'); b=p.read_bytes(); assert len(b)<=327680; p.write_bytes(b.ljust(327680,b'\xe5'))"
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdos86base.img: base.img ../boot/boottrack.bin diskdefs ../tools/cpm86twist.py Makefile
	cp base.img $@
	dd if=../boot/boottrack.bin of=$@ bs=4096 count=1 conv=notrunc 2>/dev/null

# Kernel and commands are prerequisites built by the top-level Makefile.
cdos86.img: cdos86base.img ../kernel/sysgen/ccpm.sys startup.0 $(SYSTEM_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys startup.0 $(SYSTEM_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

# Development disk, deliberately data-only for this initial media set.
cdostools.img: cdos86base.img $(TOOLS_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(TOOLS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

check: all
	@tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	set -e; for image in $(IMAGES); do \
	    $(TWIST) untwist $$image "$$tmp/logical.img"; \
	    dd if="$$tmp/logical.img" bs=4096 count=1 2>/dev/null | cmp ../boot/boottrack.bin -; \
	    $(CPMCP) "$$tmp/logical.img" 0:PIP.CMD "$$tmp/pip.cmd"; \
	    cmp $(PIP) "$$tmp/pip.cmd"; \
	    $(CPMCP) "$$tmp/logical.img" 0:SYSDISK.CMD "$$tmp/sysdisk.cmd"; \
	    cmp ../commands/sysdisk/sysdisk.cmd "$$tmp/sysdisk.cmd"; \
	done; \
	$(TWIST) untwist cdos86.img "$$tmp/logical.img"; \
	$(CPMCP) "$$tmp/logical.img" 0:CCPM.SYS "$$tmp/ccpm.sys"; \
	cmp ../kernel/sysgen/ccpm.sys "$$tmp/ccpm.sys"; \
	$(CPMCP) "$$tmp/logical.img" 0:STARTUP.0 "$$tmp/startup.0"; \
	cmp startup.0 "$$tmp/startup.0"; \
	$(TWIST) untwist cdostools.img "$$tmp/logical.img"; \
	for source in $(TOOLS_COMMANDS); do \
	    name=$${source##*/}; $(CPMCP) "$$tmp/logical.img" 0:$$name "$$tmp/$$name"; \
	    cmp $$source "$$tmp/$$name"; \
	done
	@echo 'Media: both boot tracks and packaged source-built files verified'

check-pce: check
	$(PYTHON) ../tools/boot_check.py

# Same interactive PCE test target and launcher pattern as CCP/M.
test: cdos86.img cdostools.img cdos86 cdos86.cfg
	./cdos86

clean:
	$(RM) $(IMAGES) base.img cdos86base.img *.tmp
