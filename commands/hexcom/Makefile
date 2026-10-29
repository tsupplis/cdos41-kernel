# HEXCOM — local component build.
# all builds local outputs; check validates them; clean removes generated files.

CC=aztec42_cc
LD=aztec42_link
CFLAGS=-I. +0 -D__CPM__
CPM_LDFLAGS=-lc86

.PHONY: all check clean
.DELETE_ON_ERROR:

all: binaries

OBJS=hexcom.o

binaries: hexcom.cmd

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

hexcom.cmd: $(OBJS) Makefile
	$(LD) -o $@ $(OBJS) $(CPM_LDFLAGS)

# Remove generated outputs only; preserve sources and reference files.
clean:
	rm -rf *.o *.cmd
