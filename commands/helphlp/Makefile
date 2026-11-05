# HELPHLP — indexed HELP database. Builds help.hlp from help.dat with the
# native HELP [C] indexer of ../help/help.cmd (run under emu2).

HELPCMD=../help/help.cmd

.PHONY: all check clean
.DELETE_ON_ERROR:

all: help.hlp

check: all
	python3 -B ../../tools/help_style.py help.dat

$(HELPCMD):
	$(MAKE) -C ../help help.cmd

# Same native HELP [C] indexer and temporary-text workflow as CCP/M.
help.hlp: $(HELPCMD) help.dat ../../tools/help_style.py Makefile
	python3 -B ../../tools/help_style.py help.dat
	@set -e; tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT HUP INT TERM; \
	cp $(HELPCMD) "$$tmp/help.cmd"; \
	cp help.dat "$$tmp/help.dat"; \
	unix2dos "$$tmp/help.dat"; \
	(cd "$$tmp" && EMU2_CPM_VER=4.1 emu2 help.cmd '[C]'); \
	cp "$$tmp/help.hlp" $@
	@test -s $@

clean:
	rm -f help.hlp
