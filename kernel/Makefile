# Kernel components, resident processes and system-image composition.
# The alternate XIOS is an explicit opt-in build.

SUBDIRS=con rsp1 rsp2 rsp3 sysgen

.PHONY: all check clean xios-alt
.DELETE_ON_ERROR:

all check clean:
	set -e; for d in $(SUBDIRS); do $(MAKE) -C $$d $@; done

xios-alt:
	$(MAKE) -C xios all
