#!/usr/bin/env python3
"""Check the generated 4.1 system layout and scheduler initialization."""
from pathlib import Path
import sys


def check(path):
    image = path.read_bytes()
    word = lambda b, at: int.from_bytes(b[at:at + 2], 'little')
    assert len(image) >= 128 and image[0] == 1 and image[9] == 2, 'Missing CODE/DATA groups'
    code_length, code_base = word(image, 1), word(image, 3)
    data_length, data_base = word(image, 10), word(image, 12)
    assert code_base and data_base == code_base + code_length, 'Invalid fixed group addresses'
    assert len(image) >= 128 + (code_length + data_length) * 16, 'Truncated system groups'
    data = image[128 + code_length * 16:128 + (code_length + data_length) * 16]
    assert word(data, 0x40) == code_base, 'SYSDAT OS start disagrees with header'
    assert data_base < word(data, 0x44) <= 0xa000, 'System exceeds conventional memory'
    flags, count = word(data, 0x56), data[0x4a]
    assert count and flags + count * 3 <= min(len(data), 65536), 'Flag table outside SYSDAT'
    assert data[flags:flags + count * 3] == b'\xff' * (count * 3), 'Invalid RTM flag initialization: expected FF FF FF for every entry'
    segment = word(data, 0x42)
    seen, names = set(), []
    while segment:
        assert segment not in seen, 'Circular resident-process chain'
        seen.add(segment)
        offset = 128 + (segment - code_base) * 16
        assert 128 <= offset and offset + 0x40 <= 128 + (code_length + data_length) * 16, 'Resident-process header outside file'
        header = image[offset:offset + 0x40]
        name = header[0x18:0x20].decode('ascii').rstrip()
        assert name and all(32 <= ord(c) < 127 for c in name), 'Invalid resident-process name'
        names.append(name)
        segment = word(header, 0)
    assert {'PIN', 'PCTMP', 'CONFIDD', 'CLOCK'} <= {name.upper().rstrip('0123456789') for name in names}, ('Missing resident processes', names)
    print(f'PASS: system layout, {count} RTM flags and resident-process chain: ' + ', '.join(names))


if __name__ == '__main__':
    check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('ccpm.sys'))
