# DOS date and time commands

DATE.EXE is built from the OEM 4.1 PCDATE.A86 with the documented short-year
pivot fix. Its original regression test is retained in tests/datecheck.asm;
`make check` runs 54 parser cases without changing a clock.

Native DATE.CMD is separate in commands/date. This directory is reserved for
DOS-family DATE.EXE and TIME.EXE.

TIME.EXE is reconstructed from the CDOS 4.11 executable, not recovered OEM
source. After assembly and linking, `normalize_time.py` checks the LINK86
output and restores the release's MZ size, stack segment and checksum fields.
`make check-time` compares the complete executable with `base/time.exe` and
checks the current-time line and input prompt at five synthetic times without
setting a clock. The release space-pads single-digit hours and zero-pads the
other fields.
