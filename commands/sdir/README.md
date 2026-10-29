# SDIR: Concurrent DOS 4.1 compatibility

Built from the imported CCP/M-86 3.1 PL/M sources. The original 4.1
`base/sdir.cmd` is retained as a behavioral reference. It is not used to
build this command.

## Syntax and options

`SDIR {filespec ...} [options]` accepts one grouped option list. File specs
can include a drive and wildcards; at most ten search specifications are
accepted. Commas or spaces separate options. Keywords follow the historical
parser's prefix matching. Use `SDIR [HELP]` for the compact option list.

| Options | Meaning |
| --- | --- |
| FULL / SIZE / SHORT | Detailed listing (default), names/sizes, or names only |
| DATE | Detailed listing with timestamps; requires timestamp information |
| ATTRIBUTES | Show archive and user attribute bits |
| DIR / SYS | Select non-system / system files; DIR does not mean subdirectories |
| RO / RW | Select read-only / writable entries |
| XFCB / NONXFCB | Select entries with / without password or timestamp metadata |
| SORT / NOSORT | Sort by name/type (default) / retain search order |
| EXCLUDE | Invert filename matching |
| DRIVE=d / DISK=d | Select a drive; ALL or `(A,B)` lists are supported |
| USER=n / G<n> | Select a CP/M user; USER also accepts ALL or `(0,1)` lists |
| MESSAGE | Show searched areas even when no matching entry is found |
| LENGTH=n / FF | Repeat headers after n rows (minimum 5); optionally use form feeds |
| PAGE / NOPAGE | Pause after 23 physical rows / disable pauses (default) |
| HELP | Display the option summary and exit |

`SHORT` and `HELP` were absent from the active parser in both the imported
source and the OEM 4.1 binary. SHORT's routine and both options' old help
text survived in the source. They are now exposed and documented locally.
SHORT uses the same buffered search, filters and sorting as FULL/SIZE.

## DOS directories

The 4.1 kernel translates a FAT directory entry into a CP/M-style search
result. Bytes 16 and 17 hold identical flag values: bit 80h identifies the
DOS representation and bit 40h identifies a subdirectory. The byte-0 XFCB
guard must also be checked; allocation bytes on CP/M media are not by
themselves a directory indication. See `kernel/con/black.a86`.

The original SDIR understands translated DOS sizes and timestamps, but drops
the directory flag from its buffered records. It prints directories as 0k
files. The local version preserves that flag through sorting and displays
`<DIR>` in FULL/SIZE and a backslash before directory names in SHORT/SIZE.
Directories have no regular-file byte/record size and are counted separately.
Existing CP/M DIR/SYS filtering is preserved; neither option is redefined.
Hidden entries remain visible as in the OEM command.

The internal file record grows from 23 to 24 bytes. `file$address` uses
`size(file$info)` rather than a hard-coded stride, and the memory/sort checks
use the same helper.

## Verification

`make check-sdir` at the project root runs the OEM and rebuilt commands under
PCE on disposable CP/M and FAT12 floppy images. It compares ordinary entries
and legacy options, checks both CP/M users and read-only attributes, verifies
empty/populated DOS directories and their totals, exercises SHORT/HELP, and
checks paging, NOPAGE and Ctrl-C. PUT/RDR capture the actual command output.
Directory markers/counts and SHORT/HELP are intentional differences. Physical
directory-entry usage differs as each capture creates its own log.

Explicit DOS paths and current-subdirectory traversal are not covered by this
regression yet; this is not a claim of complete filesystem compatibility.
