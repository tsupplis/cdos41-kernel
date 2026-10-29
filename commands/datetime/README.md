# DOS date and time commands

DATE.EXE is built from the OEM 4.1 PCDATE.A86 with the documented short-year
pivot fix. Its original regression test is retained in tests/datecheck.asm;
`make check` runs 54 parser cases without changing a clock.

Native DATE.CMD is separate in commands/date. This directory is reserved for
DOS-family DATE.EXE and TIME.EXE.

TIME uses bounded two-digit formatting for HH:MM:SS.hh. `make check-time`
checks the complete current-time line and input prompt at five synthetic
times, including midnight and 23:59:59.99, without setting any clock.
