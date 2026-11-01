# SDIR: Concurrent DOS 4.1 compatibility

Built from the imported CCP/M-86 3.1 PL/M sources. The independent 4.11
reference is `base/sdir411.cmd`, extracted from release disk 3. The older
`base/sdir.cmd` identifies itself as CCP/M-86 2.0 and is preserved separately;
it is not the 4.11 oracle. Neither binary is a build dependency.

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
source and the 4.11 binary. SHORT's routine and both options' old help
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

`make check-sdir` at the project root runs the 4.11 and rebuilt commands under
PCE on disposable CP/M and FAT12 floppy images. It compares ordinary entries
and legacy options, checks both CP/M users and read-only attributes, verifies
empty/populated DOS directories and their totals, exercises SHORT/HELP, and
checks paging, NOPAGE and Ctrl-C. PUT/RDR capture the actual command output.
Directory markers/counts and SHORT/HELP are intentional differences.
The original formats a 2026 timestamp as `<6`; the maintained command prints
`26`. Comparison normalizes this specific original year-format defect. Physical
directory-entry usage differs as each capture creates its own log.

The companion `tools/sdir_paths_check.py` covers seven paired path/current-
subdirectory cases. Both versions reject backslash paths with “Illegal command
tail.” Both correctly list a plain filename or wildcard on a FAT drive after
CHDIR changes that drive's current directory. SIZE is checked there as well.
Use CHDIR first (or a mapped drive), then SDIR with a drive/filespec; SDIR does
not acquire DOS pathname syntax through this alignment.

## 4.11 assessment result

The 27 paired cases on CP/M and FAT12 found no additional legacy-option gap:
default/FULL, SIZE, DATE, DIR/SYS, RO/RW, ATTRIBUTES, SORT/NOSORT,
XFCB/NONXFCB, USER/G, DRIVE/DISK, LENGTH/FF, EXCLUDE and invalid options.
The release command rejects SHORT and HELP; the maintained command implements
them. PAGE/NOPAGE and Ctrl-C were also exercised on the maintained command.

Directory rendering/counts and year formatting are improvements to retain,
not regressions to copy from the release binary. This is an assessment of
those scenarios, not complete binary equivalence. The seven additional path/subdirectory cases also pass. No production
SDIR changes were required by this assessment.
