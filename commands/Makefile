# Enable a family only after its source build has been verified.
SUBDIRS=genccpm pip rmdir sysdisk
.PHONY: all clean
all clean:
	set -e; for d in $(SUBDIRS); do $(MAKE) -C $$d $@; done
