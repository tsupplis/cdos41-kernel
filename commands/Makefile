# Enabled only after the local source build has passed.
SUBDIRS=genccpm pip asm86 gencmd submit batch chdir \
    mkdir rmdir sysdisk chset initdir help \
    function dredix copymenu editmenu printmgr dsp dskmaint \
    genldr loadccpm copy datetime erase path \
    asm80 era ren systat window date sdir show hexcom print set type dir ed disk

CMDS=genccpm/genccpm.cmd asm86/asm86.cmd gencmd/gencmd.cmd submit/submit.cmd batch/batch.cmd \
    chdir/chdir.cmd mkdir/mkdir.cmd rmdir/rmdir.cmd sysdisk/sysdisk.cmd chset/chset.cmd \
    initdir/initdir.cmd era/eraq.cmd help/help.cmd function/function.cmd dredix/dredix.cmd \
    copymenu/copymenu.cmd editmenu/editmenu.cmd printmgr/printmgr.cmd dsp/dsp.cmd dskmaint/dskmaint.cmd \
    genldr/genldr.cmd pip/pip4.cmd \
    asm80/asm80.cmd era/era.cmd ren/ren.cmd systat/systat.cmd \
    window/window.cmd window/wmenu.cmd date/date.cmd sdir/sdir.cmd show/show.cmd \
    hexcom/hexcom.cmd print/print.cmd set/set.cmd type/type.cmd dir/dir.cmd ed/ed.cmd \
    disk/dcopy.cmd disk/dcomp.cmd
DOS_EXES=copy/copy.exe datetime/date.exe erase/erase.exe path/path.exe

all clean:
	set -e; for d in $(SUBDIRS); do \
		$(MAKE) -C $$d $@; \
	done

check: all
	@set -e; for f in $(CMDS); do cmdinfo $$f; done
	@python3 -c "from pathlib import Path; files='$(DOS_EXES)'.split(); assert all(Path(f).read_bytes()[:2]==b'MZ' for f in files), 'Expected DOS EXE header'; assert Path('loadccpm/loadccpm.com').read_bytes()[0]==0xe9, 'Expected LOADCCPM entry JMP'"
	$(MAKE) -C gencmd check
	$(MAKE) -C dskmaint check-boot
	$(MAKE) -C datetime check-date

.PHONY: all check clean $(SUBDIRS)
