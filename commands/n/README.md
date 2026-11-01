# N.CMD

Run N from a local console to select a language and configure national
keyboard, screen and printer settings. The utility reads NATIONAL.MSG for
its menus and updates CCPM.SYS. There is no command-tail option parser.

## Kernel interface

After checking BDOS function 12, N reads the word at byte 1 of CCPM.SYS.
It multiplies this paragraph count by 16 and adds 80h to locate the DATA
group. For the 4.11 layout it expects the word 574Ah at DATA + 0C3Ch.
The next word points to 24 DATA-relative offsets. A zero offset marks a
missing table. N converts the other offsets to file positions. Its update
routines use the directory to write strings and fixed-size blocks.

The release kernel on disk 1 contains the signature at file offset 989Ch.
The rebuilt kernel examined during reconstruction contained 00 FC at its
corresponding offset A9FCh. National configuration requires a compatible
directory and working kernel consumers for its entries.

## Build and verification

The source contains the application and the linked Digital Research
small-model C runtime. ASM86 assembles the instructions. GENCMD supplies
the two-group executable, and encodings.py restores the DATA growth limit
and 21 alternate register-to-register encodings. The checker compares the
complete 8,704-byte result with the retained 4.11 disk 1 reference.
Run `make check` in this directory.

## Read-only C probe

Build with `make nprobe.cmd`. Run NPROBE with the target 4.11 CCPM.SYS in
the current directory. It opens the file read-only, prints the 24 directory
entries relative to DATA, then prints the keyboard/screen choice in English.
The release disk 1 file selects index 1 (U.K., 8 Bit). The rebuilt kernel
fails the JW check before the directory is read.

The following slot numbers are decimal. Sizes and source indices come from
the arguments to write_block_slot and write_string_slot in N.CMD. String
writes include the terminating zero. Message data indices refer to the
installation data selected from NATIONAL.MSG.

| Slots | Use by N |
| --- | --- |
| 0 | One byte from the language selection variable |
| 1 | One byte looked up using the keyboard/screen selection |
| 2 | One byte containing the keyboard/screen selection itself |
| 3–5 | Three 54-byte keyboard translation blocks, data indices 0–2 or 13–15 |
| 6–8 | Three strings from data indices 3–5 |
| 9 | String from data index 6 or 16 |
| 10 | Five 11-byte printer/device records |
| 11–12 | Two 48-byte blocks from data indices 7 and 8 |
| 13 | Five bytes from data index 9 |
| 14 | Language description string (message zero) |
| 15 | Five bytes from data index 10 |
| 16–17 | Two eight-byte blocks from data indices 11 and 12 |
| 18 | One byte from the selection variable at DATA 0500h |
| 19–20 | Two strings from data indices 17–18 or 19–20 |
| 21–23 | Zero entries on release disk 1, unused by the save routine |

## Keyboard save comparison

Build with `make nkey.cmd`. Supply NATIONAL.MSG and a disposable kernel
named NTEST.SYS. Run `NKEY keyboard [language]`, with keyboard 0–4 and
language 0–8 (the NATIONAL.MSG directory index). Omitting language
preserves the kernel's current selection. NKEY prepares the complete save
across slots 0–20, keeping the existing printer selections. It stages the
original and replacement data before writing.

Run `python3 check_save.py /path/to/release/CCPM.SYS` after building NKEY.
The test scripts the menu choices and save confirmation in a temporary
copy of the release command. Its file readers, save instructions and BDOS
writes execute under cpm86. Both programs operate on temporary kernel
copies. The test compares all resulting bytes for nine languages, five
keyboard choices and both values of the alternate-table switch.

## Keyboard consumers in the IBM PC XIOS

The 4.11 release keeps two banks of three 84-byte scan-code tables.
Offsets below are relative to the release DATA group. The rebuilt symbol
offsets come from the XIOS assembly listing and use its own segment origin.

| Scan-code map | Fixed bank | National bank | Rebuilt XIOS symbol |
| --- | ---: | ---: | --- |
| Plain | 6FBEh | 70BAh (slot 3) | key_table, 13FEh |
| Shift | 7012h | 710Eh (slot 4) | shift_table, 1452h |
| Control | 7066h | 7162h (slot 5) | control_table, 14A6h |

All 252 bytes of the rebuilt maps match the release fixed bank. N writes
the first 54 bytes of each national map, covering scan codes 0–53. The
remaining 30 bytes of each map include function and keypad translations.

At release file offset F8C2h the selector indexes the five mode bytes
00h, 06h, 01h, 07h, 03h using the keyboard selection (slot 2), stores
the result in slot 1 and tests bit 1. Clear selects the fixed bank, set
selects the national bank. It installs plain, Shift and Control pointers
at DATA offsets 6D3Eh, 6D40h and 6D42h. The interrupt handler loads BX
through those pointers before XLAT. Shift also has a Num Lock/keypad path.

The rebuilt IBM PC XIOS now initializes the three pointers in
select_key_bank before installing its interrupt vectors. The plain,
Control, Shift and Num Lock paths use those pointers. The fixed bank
remains the default and the separate national bank holds the UK release
maps. The national directory and the remaining consumers are still pending.

## Printer records and the XIOS output path

Slot 10 addresses five 11-byte records at release DATA 6DB6h. A separate
pointer table at 6DACh indexes LPT1–3 and COM1–2 in that order.
The release list-output entry at 71B6h accepts the character in CL and
device number in DL, rejects device numbers above four, loads the record
pointer, then jumps through the handler word at record offset 4.

| Record offset | Purpose |
| --- | --- |
| 0 | Physical printer number passed to the output driver |
| 1 | Model index: IBM Graphics, Epson MX, Epson MX with Graftrax, Epson FX, daisy wheel, or no translation (0–5) |
| 2–3 | Model flags, set by N to 4, 2, 4, 7, 1 or 0 respectively |
| 4–5 | Current output handler or continuation for a multi-byte escape sequence |
| 6–7 | Count used while passing escape-sequence parameters or data |
| 8 | Last character-set selection sent with ESC R; N resets it to FFh |
| 9–10 | Translated character and auxiliary translation byte |

On disk all five handlers point to 71D1h. Model 5 installs the direct
writer at 7383h on its first character. Other models inspect ESC sequences
and translate characters according to the flags and national tables.
For example, the daisy-wheel path at 7294h maps characters 80h–AFh
through slots 12 and 11. The UK seven-bit substitution at 738Bh searches
slot 7 and substitutes the corresponding byte from slot 8. Slots 16 and
17 are consulted during escape-sequence handling.

The release direct writer reloads DL from record byte zero and calls
4281h. The rebuilt io_list now enters the same per-device translation
state machine. Its pr_emit calls physical_list, which dispatches to
parallel_out, serial_out or null_out. list_data still holds physical port
addresses and serial numbers. The default model is transparent on all
five devices.
