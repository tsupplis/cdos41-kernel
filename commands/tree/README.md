# TREE

`TREE {d:}` lists every directory from the root of a DOS/FAT drive. Each row
shows the sum of immediate regular-file byte lengths, its file count and its
full path. Child totals are not added to parents. Directory entries, `.` and
`..` are not files. Order follows the disk, as in DOS Plus TREE.

This is a new native C implementation of the DOS Plus interface, not a
byte-identical reconstruction. `TREE [HELP]` describes the syntax. CP/M disks
are rejected because they have user areas rather than hierarchical directories.
The native directory mappings belong to TREE; the shell's directory is retained.

Paths are limited to 67 characters by the CDOS directory interface. A directory
whose total byte length overflows 32 bits is reported as an error. Traversal
rescans the parent after each child, avoiding an unbounded directory list or
simultaneously open files. Output uses native console calls, so PUT can capture it.

Build with `make`; validate with `make check` and root `make check-tree`.
