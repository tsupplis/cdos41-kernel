"""Apply/check the DOSBOOT insertion described by the original DSKMAINT.SUB."""
from pathlib import Path
import sys

raw = Path('dskraw.cmd').read_bytes()
boot = Path('dosboot.bin').read_bytes()
marker = b'PUT THE PC LOADER HERE'
assert len(boot) == 512, 'DOSBOOT must be exactly one sector'
assert raw.count(marker) == 1, 'Expected one PC_LOADER placeholder'
start = raw.index(marker)
# The insertion must stay inside a loaded CODE or DATA group.
pos = 128
ranges = []
for at in range(0, 72, 9):
    kind = raw[at]
    if not kind:
        break
    size = int.from_bytes(raw[at + 1:at + 3], 'little') * 16
    if kind in (1, 2):
        ranges.append((pos, pos + size))
    pos += size
assert any(a <= start and start + 512 <= b for a, b in ranges), 'Loader outside CODE/DATA'
expected = raw[:start] + boot + raw[start + 512:]
if '--check' in sys.argv:
    assert Path('dskmaint.cmd').read_bytes() == expected, 'Unexpected DSKMAINT bytes'
    print('PASS: DOSBOOT is embedded; every other CMD byte is unchanged')
else:
    Path('dskmaint.cmd').write_bytes(expected)
