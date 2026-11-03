# Build the eight distribution disks from local components and reference files.
# check validates image contents; test starts the configured PCE machine.

PYTHON ?= python3
FORMAT=ccpm86-320
TWIST=$(PYTHON) ../tools/cpm86twist.py
CPMCP=cpmcp -f $(FORMAT)
IMAGES=cdos86.img cdostools.img cdosdev.img cdosmaint.img cdosmenu.img cdosdos.img cdosextras.img cdosadmin.img
PIP=../commands/pip/pip4.cmd

SYSTEM_COMMANDS = ../commands/batch/batch.cmd ../commands/era/era.cmd \
    ../commands/chdir/chdir.cmd ../commands/mkdir/mkdir.cmd ../commands/rmdir/rmdir.cmd \
    ../commands/era/eraq.cmd ../commands/ren/ren.cmd ../commands/date/date.cmd \
    ../commands/sdir/sdir.cmd ../commands/show/show.cmd ../commands/set/set.cmd \
    ../commands/type/type.cmd ../commands/dir/dir.cmd \
    ../commands/ed/ed.cmd ../commands/rename/ren.exe ../commands/stop/stop.cmd

# Development tools are kept separate from day-to-day utilities.
DEV_COMMANDS = ../commands/asm80/asm80.cmd ../commands/asm86/asm86.cmd \
    ../commands/ddt86/ddt86.cmd ../commands/gencmd/gencmd.cmd \
    ../commands/hexcom/hexcom.cmd ../commands/genccpm/genccpm.cmd \
    ../commands/genldr/genldr.cmd ../commands/ed/ed.cmd ../commands/submit/submit.cmd

TOOLS_COMMANDS = ../commands/submit/submit.cmd ../commands/tree/tree.cmd ../commands/echo/echo.cmd \
    ../commands/putget/put.cmd ../commands/putget/get.cmd ../commands/putget/rdr.cmd \
    ../commands/era/era.cmd \
    ../commands/help/help.cmd ../commands/helphlp/help.hlp ../commands/systat/systat.cmd \
    ../commands/chset/chset.cmd ../commands/window/window.cmd ../commands/window/wmenu.cmd

MAINT_COMMANDS = ../commands/sysdisk/sysdisk.cmd ../commands/era/era.cmd \
    ../commands/dskmaint/dskmaint.cmd ../commands/hdmaint/hdmaint.cmd \
    ../commands/initdir/initdir.cmd

MENU_COMMANDS = ../commands/spl/spl.cmd ../commands/print/print.cmd ../commands/dredix/dredix.cmd ../commands/copymenu/copymenu.cmd ../commands/editmenu/editmenu.cmd \
    ../commands/printmgr/printmgr.cmd ../commands/dsp/dsp.cmd ../base/term.dat \
    ../base/menu.dat ../base/fdmenu.dat ../base/hdmenu.dat \
    ../base/index.dsp ../commands/dredix/help.edx \
    ../commands/dredix/lsn.edx ../base/keys.pfk ../base/carddeck.bat \
    ../base/clear.bat \
    ../base/user.txt

DOS_COMMANDS = ../commands/loadccpm/loadccpm.com ../commands/setenv/setenv.cmd ../commands/batch/batch.cmd ../commands/era/era.cmd \
    ../commands/copy/copy.exe ../commands/datetime/date.exe ../commands/erase/erase.exe \
    ../commands/path/path.exe ../commands/datetime/time.exe ../commands/rename/ren.exe \
    ../commands/redos/redos.com

EXTRAS_COMMANDS = ../extra/back.cmd ../extra/rest.cmd ../extra/brinst.cmd \
    ../extra/cardfile.cmd ../extra/cardfile.dis ../extra/cardfile.trm ../extra/control.br ../extra/drtalk.exe \
    ../extra/drtalk.def ../extra/drtalk.dir ../extra/drtalk.key

ADMIN_COMMANDS = ../commands/function/function.cmd ../commands/disk/dcopy.cmd ../commands/disk/dcomp.cmd \
    ../commands/n/n.cmd ../base/national.msg \
    ../commands/setport/setport.cmd ../commands/setup/setup.cmd \
    ../commands/stop/stop.cmd \
    ../commands/chkcpmfs/chkcpmfs.cmd ../extra/fm.cmd ../extra/fm.cfg ../base/term.dat

.PHONY: all check check-media check-pce test clean
.DELETE_ON_ERROR:

all: $(IMAGES)

# Keep the empty filesystem template, but always install the source-built boot.
cdos86base.img: base.img ../boot/boottrack.bin diskdefs ../tools/cpm86twist.py Makefile
	cp base.img $@
	dd if=../boot/boottrack.bin of=$@ bs=4096 count=1 conv=notrunc 2>/dev/null

# Commands/kernel are built by the project root; these rules package outputs.

cdos86.img: cdos86base.img ../kernel/sysgen/ccpm.sys $(SYSTEM_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys $(SYSTEM_COMMANDS) 0:
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
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosdev.img: cdos86base.img $(DEV_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(DEV_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosmaint.img: cdos86base.img ../kernel/sysgen/ccpm.sys $(MAINT_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys $(MAINT_COMMANDS) 0:
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

cdosextras.img: cdos86base.img $(EXTRAS_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(EXTRAS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosadmin.img: cdos86base.img $(ADMIN_COMMANDS) $(PIP) Makefile
	$(TWIST) untwist cdos86base.img $@.logical.tmp
	$(CPMCP) $@.logical.tmp $(ADMIN_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

# Compare all payload bytes. CP/M may append only record-alignment padding.
check check-media: all
	@set -e; for image in $(IMAGES); do \
	    $(TWIST) untwist $$image $$image.verify.tmp; \
	    dd if=$$image of=$$image.boot.tmp bs=4096 count=1 2>/dev/null; \
	    cmp $$image.boot.tmp ../boot/boottrack.bin; \
	    test "$$(wc -c < $$image)" -eq 327680; \
	    case $$image in \
	      cdos86.img) sources='../kernel/sysgen/ccpm.sys $(SYSTEM_COMMANDS)' ;; \
	      cdostools.img) sources='$(TOOLS_COMMANDS)' ;; \
	      cdosdev.img) sources='$(DEV_COMMANDS)' ;; \
	      cdosmaint.img) sources='../kernel/sysgen/ccpm.sys $(MAINT_COMMANDS)' ;; \
	      cdosmenu.img) sources='$(MENU_COMMANDS)' ;; \
	      cdosdos.img) sources='$(DOS_COMMANDS)' ;; \
	      cdosextras.img) sources='$(EXTRAS_COMMANDS)' ;; \
	      cdosadmin.img) sources='$(ADMIN_COMMANDS)' ;; \
	    esac; \
	    for source in $$sources $(PIP); do \
	        name=$${source##*/}; if test "$$source" = "$(PIP)"; then name=PIP.CMD; fi; \
	        $(CPMCP) $$image.verify.tmp 0:$$name $$image.file.tmp; \
	        $(PYTHON) -c "from pathlib import Path; a=Path('$$source').read_bytes(); b=Path('$$image.file.tmp').read_bytes(); assert b[:len(a)]==a and all(c in (0,26) for c in b[len(a):]), '$$image: $$name differs'"; \
	    done; \
	    $(RM) $$image.verify.tmp $$image.file.tmp $$image.boot.tmp; \
	    echo "$$image: every payload, boot track and size verified"; \
	done

check-pce: check
	$(PYTHON) ../tools/boot_check.py

# Same launcher/configuration convention as CCP/M: A=system, B=tools.
test: cdos86.img cdostools.img cdos86 cdos86.cfg
	./cdos86

# Remove generated outputs only; preserve sources and reference files.
clean:
	$(RM) cdos86base.img $(IMAGES) *.img.*.tmp *.img.tmp
