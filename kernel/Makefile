SUBDIRS=con rsp1 rsp2 rsp3
.PHONY: all clean xios-alt
all clean:
	set -e; for d in $(SUBDIRS); do $(MAKE) -C $$d $@; done
xios-alt:
	$(MAKE) -C xios all
