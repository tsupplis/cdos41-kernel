# Build the eight distribution disks from local components and reference files.
# check validates image contents; test starts the configured PCE machine.

PYTHON ?= python3
FORMAT=ccpm86-320
TWIST=$(PYTHON) ../tools/cpm86twist.py
CPMCP=cpmcp -f $(FORMAT)
SMALL_IMAGES = cdos86.img cdostools.img cdosdev.img cdosmaint.img cdosmenu.img cdosdos.img cdosextras.img cdosadmin.img
LARGE_IMAGES = cdos86-1440.img
IMAGES = $(SMALL_IMAGES) $(LARGE_IMAGES)
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
    ../commands/dskmaint/dskmaint.cmd ../commands/dform/dform.cmd ../commands/hdmaint/hdmaint.cmd \
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
    ../commands/path/path.cmd ../commands/datetime/time.exe ../commands/rename/ren.exe \
    ../commands/redos/redos.com ../commands/chkdosfs/chkdosfs.cmd

EXTRAS_COMMANDS = ../extra/back.cmd ../extra/rest.cmd ../extra/brinst.cmd \
    ../extra/cardfile.cmd ../extra/cardfile.dis ../extra/cardfile.trm ../extra/control.br ../extra/drtalk.exe \
    ../extra/drtalk.def ../extra/drtalk.dir ../extra/drtalk.key

ADMIN_COMMANDS = ../commands/function/function.cmd ../commands/disk/dcopy.cmd ../commands/disk/dcomp.cmd \
    ../commands/n/n.cmd ../base/national.msg \
    ../commands/setport/setport.cmd ../commands/setup/setup.cmd \
    ../commands/stop/stop.cmd \
    ../commands/chkcpmfs/chkcpmfs.cmd ../commands/fm/fm.cmd ../extra/fm.cfg ../base/term.dat

.PHONY: all check check-media check-pce test clean
.DELETE_ON_ERROR:

all: $(IMAGES)

# On-demand empty physical fixture for existing tests.
cdos86base.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(TWIST) twist $@.logical.tmp $@
	$(RM) $@.logical.tmp

# Commands/kernel are built by the project root; these rules package outputs.

cdos86.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs ../kernel/sysgen/ccpm.sys $(SYSTEM_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys $(SYSTEM_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdostools.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs $(TOOLS_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp $(TOOLS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosdev.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs $(DEV_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp $(DEV_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosmaint.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs ../kernel/sysgen/ccpm.sys $(MAINT_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp ../kernel/sysgen/ccpm.sys $(MAINT_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosmenu.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs $(MENU_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp $(MENU_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosdos.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs $(DOS_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp $(DOS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmchattr -f $(FORMAT) $@.logical.tmp s 0:BATCH.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosextras.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs $(EXTRAS_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp $(EXTRAS_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

cdosadmin.img: ../tools/mk320.py ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs $(ADMIN_COMMANDS) $(PIP) Makefile
	$(PYTHON) ../tools/mk320.py $@.logical.tmp --format ccpm86-320 \
	    --boot ../commands/dskmaint/bootsect.bin --loader ../commands/dskmaint/loader.bin
	$(CPMCP) $@.logical.tmp $(ADMIN_COMMANDS) 0:
	$(CPMCP) $@.logical.tmp $(PIP) 0:PIP.CMD
	cpmls -F -f $(FORMAT) $@.logical.tmp '0:*.*'
	$(TWIST) twist $@.logical.tmp $@.tmp
	mv $@.tmp $@
	$(RM) $@.logical.tmp

# Compare all payload bytes. CP/M may append only record-alignment padding.
check check-media: all check-large
	@set -e; for image in $(SMALL_IMAGES); do \
	    $(TWIST) untwist $$image $$image.verify.tmp; \
	    dd if=$$image of=$$image.boot.tmp bs=4096 count=1 2>/dev/null; \
	    cmp $$image.boot.tmp ../commands/dskmaint/boottrack.bin; \
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

# Keep all regular tools except EDITMENU; legacy extras remain on cdosextras.
LARGE_MENU_COMMANDS = ../commands/spl/spl.cmd ../commands/print/print.cmd \
    ../commands/dredix/dredix.cmd ../commands/copymenu/copymenu.cmd \
    ../commands/printmgr/printmgr.cmd ../commands/dsp/dsp.cmd ../base/term.dat \
    ../base/menu.dat ../base/fdmenu.dat ../base/hdmenu.dat ../base/index.dsp \
    ../commands/dredix/help.edx ../commands/dredix/lsn.edx ../base/keys.pfk \
    ../base/carddeck.bat ../base/clear.bat ../base/user.txt
LARGE_COMMANDS = ../commands/batch/batch.cmd ../commands/era/era.cmd ../commands/chdir/chdir.cmd \
    ../commands/mkdir/mkdir.cmd ../commands/rmdir/rmdir.cmd ../commands/era/eraq.cmd \
    ../commands/ren/ren.cmd ../commands/date/date.cmd ../commands/sdir/sdir.cmd \
    ../commands/show/show.cmd ../commands/set/set.cmd ../commands/type/type.cmd \
    ../commands/dir/dir.cmd ../commands/ed/ed.cmd ../commands/rename/ren.exe \
    ../commands/stop/stop.cmd ../commands/asm80/asm80.cmd ../commands/asm86/asm86.cmd \
    ../commands/ddt86/ddt86.cmd ../commands/gencmd/gencmd.cmd ../commands/hexcom/hexcom.cmd \
    ../commands/genccpm/genccpm.cmd ../commands/genldr/genldr.cmd ../commands/submit/submit.cmd \
    ../commands/tree/tree.cmd ../commands/echo/echo.cmd ../commands/putget/put.cmd \
    ../commands/putget/get.cmd ../commands/putget/rdr.cmd ../commands/help/help.cmd \
    ../commands/helphlp/help.hlp ../commands/systat/systat.cmd ../commands/chset/chset.cmd \
    ../commands/window/window.cmd ../commands/window/wmenu.cmd ../commands/sysdisk/sysdisk.cmd \
    ../commands/dskmaint/dskmaint.cmd ../commands/dform/dform.cmd ../commands/hdmaint/hdmaint.cmd \
    ../commands/initdir/initdir.cmd ../commands/loadccpm/loadccpm.com ../commands/setenv/setenv.cmd \
    ../commands/copy/copy.exe ../commands/datetime/date.exe ../commands/erase/erase.exe \
    ../commands/path/path.cmd ../commands/datetime/time.exe ../commands/redos/redos.com \
    ../commands/chkdosfs/chkdosfs.cmd ../commands/function/function.cmd ../commands/disk/dcopy.cmd \
    ../commands/disk/dcomp.cmd ../commands/n/n.cmd ../base/national.msg \
    ../commands/setport/setport.cmd ../commands/setup/setup.cmd ../commands/chkcpmfs/chkcpmfs.cmd \
    ../commands/fm/fm.cmd ../extra/fm.cfg ../base/term.dat \
    ../commands/spl/spl.cmd ../commands/print/print.cmd ../commands/dredix/dredix.cmd \
    ../commands/copymenu/copymenu.cmd ../commands/printmgr/printmgr.cmd ../commands/dsp/dsp.cmd \
    ../base/menu.dat ../base/fdmenu.dat ../base/hdmenu.dat \
    ../base/index.dsp ../commands/dredix/help.edx ../commands/dredix/lsn.edx \
    ../base/keys.pfk ../base/carddeck.bat ../base/clear.bat \
    ../base/user.txt

# Native 1.44MB physical images: libdsk maps head order; no 320K twist.
cdos86-1440.img: ../kernel/sysgen/ccpm.sys $(LARGE_COMMANDS) ../commands/pip/pip4.cmd ../commands/dskmaint/bootsect.bin ../commands/dskmaint/loader.bin diskdefs Makefile
	$(PYTHON) -c "import sys; sys.stdout.buffer.write(b'\xe5' * 1474560)" > $@.tmp
	mkfs.cpm -f cpm86-1440 $@.tmp
	dd if=../commands/dskmaint/bootsect.bin of=$@.tmp bs=1 conv=notrunc 2>/dev/null
	printf '\001\220' | dd of=$@.tmp bs=1 seek=510 conv=notrunc 2>/dev/null
	dd if=../commands/dskmaint/loader.bin of=$@.tmp bs=1 seek=2304 conv=notrunc 2>/dev/null
	cpmcp -T raw -f cpm86-1440 $@.tmp ../kernel/sysgen/ccpm.sys 0:CCPM.SYS
	cpmcp -T raw -f cpm86-1440 $@.tmp $(LARGE_COMMANDS) 0:
	cpmcp -T raw -f cpm86-1440 $@.tmp ../commands/pip/pip4.cmd 0:PIP.CMD
	cpmchattr -T raw -f cpm86-1440 $@.tmp s 0:BATCH.CMD
	cpmls -T raw -F -f cpm86-1440 $@.tmp '0:*.*'
	mv $@.tmp $@

.PHONY: check-large
check-large: $(LARGE_IMAGES)
	@set -e; for image in $(LARGE_IMAGES); do \
	    $(PYTHON) -c "from pathlib import Path; b=Path('$$image').read_bytes(); boot=Path('../commands/dskmaint/bootsect.bin').read_bytes(); loader=Path('../commands/dskmaint/loader.bin').read_bytes(); assert len(b)==1474560 and b[:len(boot)]==boot and b[510:512]==bytes((1,144)) and b[2304:2304+len(loader)]==loader, '$$image: boot/size mismatch'"; \
	    case $$image in \
	      cdos86-1440.img) sources='../kernel/sysgen/ccpm.sys $(LARGE_COMMANDS) ../commands/pip/pip4.cmd' ;; \
	    esac; \
	    for source in $$sources; do \
	        name=$${source##*/}; \
	        case $$name in ccpm-native.sys) name=CCPM.SYS ;; pip4.cmd) name=PIP.CMD ;; esac; \
	        cpmcp -T raw -f cpm86-1440 $$image 0:$$name $$image.file.tmp; \
	        $(PYTHON) -c "from pathlib import Path; a=Path('$$source').read_bytes(); b=Path('$$image.file.tmp').read_bytes(); assert b[:len(a)]==a and all(c in (0,26) for c in b[len(a):]), '$$image: $$name differs'"; \
	    done; \
	    cpmls -T raw -A -f cpm86-1440 $$image 0:batch.cmd | grep -q '^....s.... batch.cmd$$'; \
	    $(RM) $$image.file.tmp; \
	    echo "$$image: every payload, boot code, marker, loader and size verified"; \
	done
