# Build the seven distribution disks from local components and reference files.
# check validates image contents; test starts the configured PCE machine.

PYTHON ?= python3
FORMAT=ccpm86-320
TWIST=$(PYTHON) ../tools/cpm86twist.py
CPMCP=cpmcp -f $(FORMAT)
IMAGES=cdos86.img cdostools.img cdosmaint.img cdosmenu.img cdosdos.img cdosoem1.img cdosoem2.img
PIP=../commands/pip/pip4.cmd

SYSTEM_COMMANDS = ../commands/batch/batch.cmd ../commands/sysdisk/sysdisk.cmd ../commands/era/era.cmd \
    ../commands/chdir/chdir.cmd ../commands/mkdir/mkdir.cmd ../commands/rmdir/rmdir.cmd \
    ../commands/era/eraq.cmd ../commands/ren/ren.cmd ../commands/date/date.cmd \
    ../commands/sdir/sdir.cmd ../commands/show/show.cmd ../commands/set/set.cmd \
    ../commands/submit/submit.cmd ../commands/type/type.cmd ../commands/dir/dir.cmd \
    ../commands/ed/ed.cmd ../base/ren.exe ../base/stop.cmd \
    ../commands/putget/put.cmd ../commands/putget/get.cmd ../commands/putget/rdr.cmd

TOOLS_COMMANDS = ../commands/batch/batch.cmd ../commands/sysdisk/sysdisk.cmd ../commands/era/era.cmd \
    ../commands/asm80/asm80.cmd ../commands/asm86/asm86.cmd ../commands/gencmd/gencmd.cmd \
    ../commands/genccpm/genccpm.cmd ../commands/hexcom/hexcom.cmd ../commands/help/help.cmd \
    ../commands/help/help.hlp ../commands/print/print.cmd ../commands/systat/systat.cmd \
    ../commands/chset/chset.cmd ../commands/genldr/genldr.cmd ../commands/loadccpm/loadccpm.com \
    ../commands/window/window.cmd ../commands/window/wmenu.cmd

MAINT_COMMANDS = ../commands/batch/batch.cmd ../commands/sysdisk/sysdisk.cmd ../commands/era/era.cmd \
    ../commands/dskmaint/dskmaint.cmd ../commands/disk/dcopy.cmd ../commands/disk/dcomp.cmd \
    ../commands/initdir/initdir.cmd

MENU_COMMANDS = ../commands/dredix/dredix.cmd ../commands/copymenu/copymenu.cmd ../commands/editmenu/editmenu.cmd \
    ../commands/printmgr/printmgr.cmd ../commands/dsp/dsp.cmd ../base/term.dat \
    ../base/menu.dat ../base/fdmenu.dat ../base/hdmenu.dat \
    ../base/national.msg ../base/index.dsp ../commands/dredix/help.edx \
    ../commands/dredix/lsn.edx ../base/keys.pfk ../base/carddeck.bat \
    ../base/clear.bat \
    ../base/user.txt

DOS_COMMANDS = ../commands/batch/batch.cmd ../commands/sysdisk/sysdisk.cmd ../commands/era/era.cmd \
    ../commands/copy/copy.exe ../commands/datetime/date.exe ../commands/erase/erase.exe \
    ../commands/path/path.exe ../commands/datetime/time.exe ../base/ren.exe \
    ../base/redos.com

OEM1_COMMANDS = ../base/back.cmd ../base/rest.cmd ../base/brinst.cmd \
    ../base/control.br ../base/backrest.doc ../base/fm.cmd \
    ../base/fm.cfg ../base/spl.cmd

OEM2_COMMANDS = ../commands/function/function.cmd ../commands/help/help.cmd ../base/diskstat.cmd \
    ../base/n.cmd \
    ../commands/setport/setport.cmd ../base/setup.cmd \
    ../base/stop.cmd ../base/hdmaint.cmd \
    ../base/hdmaint.doc ../commands/help/help.hlp

.PHONY: all check check-media check-pce test clean
.DELETE_ON_ERROR:

all: $(IMAGES)

# Locally generated filesystem, then the source-built reserved boot track.
# Packaging follows CCP/M: untwist, populate, twist to physical CHS.
base.img: diskdefs Makefile
	mkfs.cpm -f $(FORMAT) $@.logical.tmp
	$(PYTHON) -c "from pathlib import Path; p=Path('$@.logical.tmp'); b=p.read_bytes(); assert len(b)<=327680; p.write_bytes(b.ljust(327680,b'\xe5'))"
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdos86base.img: base.img ../boot/boottrack.bin diskdefs ../tools/cpm86twist.py Makefile
	cp base.img $@
	dd if=../boot/boottrack.bin of=$@ bs=4096 count=1 conv=notrunc 2>/dev/null

# Commands/kernel are built by the project root; these rules package outputs.

cdos86.img: cdos86base.img ../kernel/sysgen/ccpm.sys startup.0 $(SYSTEM_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys startup.0 $(SYSTEM_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdostools.img: cdos86base.img $(TOOLS_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(TOOLS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosmaint.img: cdos86base.img ../kernel/sysgen/ccpm.sys startup.0 $(MAINT_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys startup.0 $(MAINT_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosmenu.img: cdos86base.img $(MENU_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(MENU_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosdos.img: cdos86base.img $(DOS_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(DOS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosoem1.img: cdos86base.img $(OEM1_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(OEM1_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosoem2.img: cdos86base.img $(OEM2_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(OEM2_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

# Compare all payload bytes. CP/M may append only record-alignment padding.
check check-media: all
	@set -e; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	for image in $(IMAGES); do \
	    $(TWIST) untwist $$image "$$tmp/logical.img"; \
	    dd if="$$tmp/logical.img" bs=4096 count=1 2>/dev/null | cmp ../boot/boottrack.bin -; \
	    $(PYTHON) -c "from pathlib import Path; assert Path('$$image').stat().st_size==327680"; \
	    case $$image in \
	      cdos86.img) sources='../kernel/sysgen/ccpm.sys startup.0 $(SYSTEM_COMMANDS)' ;; \
	      cdostools.img) sources='$(TOOLS_COMMANDS)' ;; \
	      cdosmaint.img) sources='../kernel/sysgen/ccpm.sys startup.0 $(MAINT_COMMANDS)' ;; \
	      cdosmenu.img) sources='$(MENU_COMMANDS)' ;; \
	      cdosdos.img) sources='$(DOS_COMMANDS)' ;; \
	      cdosoem1.img) sources='$(OEM1_COMMANDS)' ;; \
	      cdosoem2.img) sources='$(OEM2_COMMANDS)' ;; \
	    esac; \
	    for source in $$sources $(PIP); do \
	        name=$${source##*/}; if test "$$source" = "$(PIP)"; then name=PIP.CMD; fi; \
	        $(CPMCP) "$$tmp/logical.img" 0:$$name "$$tmp/file"; \
	        $(PYTHON) -c "from pathlib import Path; a=Path('$$source').read_bytes(); b=Path('$$tmp/file').read_bytes(); assert b[:len(a)]==a and all(c in (0,26) for c in b[len(a):]), '$$image: $$name differs'"; \
	    done; \
	    echo "$$image: every payload, boot track and size verified"; \
	done

check-pce: check
	$(PYTHON) ../tools/boot_check.py

# Same launcher/configuration convention as CCP/M: A=system, B=tools.
test: cdos86.img cdostools.img cdos86 cdos86.cfg
	./cdos86

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) $(IMAGES) base.img cdos86base.img *.tmp
