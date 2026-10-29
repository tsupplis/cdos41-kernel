# Enabled only after the local source build has passed.
SUBDIRS=genccpm pip asm86 gencmd submit batch chdir \
    mkdir rmdir sysdisk chset initdir help ddt86 \
    function dredix copymenu editmenu printmgr dsp dskmaint \
    genldr loadccpm copy datetime erase path rename setenv \
    asm80 era ren systat window date sdir show hexcom print set type dir ed disk putget setport

CMDS=genccpm/genccpm.cmd asm86/asm86.cmd ddt86/ddt86.cmd gencmd/gencmd.cmd submit/submit.cmd batch/batch.cmd \
    chdir/chdir.cmd mkdir/mkdir.cmd rmdir/rmdir.cmd sysdisk/sysdisk.cmd chset/chset.cmd \
    initdir/initdir.cmd era/eraq.cmd help/help.cmd function/function.cmd dredix/dredix.cmd \
    copymenu/copymenu.cmd editmenu/editmenu.cmd printmgr/printmgr.cmd dsp/dsp.cmd dskmaint/dskmaint.cmd \
    genldr/genldr.cmd pip/pip4.cmd \
    asm80/asm80.cmd era/era.cmd ren/ren.cmd systat/systat.cmd \
    window/window.cmd window/wmenu.cmd date/date.cmd sdir/sdir.cmd show/show.cmd \
    hexcom/hexcom.cmd print/print.cmd set/set.cmd type/type.cmd dir/dir.cmd ed/ed.cmd \
    disk/dcopy.cmd disk/dcomp.cmd putget/put.cmd putget/get.cmd putget/rdr.cmd setport/setport.cmd
DOS_EXES=setenv/setenv.exe copy/copy.exe datetime/date.exe datetime/time.exe erase/erase.exe path/path.exe rename/ren.exe

.PHONY: all check clean
.DELETE_ON_ERROR:

all clean:
	set -e; for d in $(SUBDIRS); do \
		$(MAKE) -C $$d $@; \
	done

check: all
	@set -e; for d in $(SUBDIRS); do $(MAKE) -C $$d check; done
	@set -e; for f in $(CMDS); do cmdinfo $$f; done
	@python3 -c "from pathlib import Path; files='$(DOS_EXES)'.split(); assert all(Path(f).read_bytes()[:2]==b'MZ' for f in files), 'Expected DOS EXE header'; assert Path('loadccpm/loadccpm.com').read_bytes()[0]==0xe9, 'Expected LOADCCPM entry JMP'"
