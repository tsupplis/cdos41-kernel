#!/usr/bin/env python3
"""Check the generated 4.1 system layout and scheduler initialization."""
from pathlib import Path
import argparse


def resident_names(image):
    """Read and validate the resident chain without assuming optional RSPs."""
    word = lambda b, at: int.from_bytes(b[at:at+2], 'little')
    code_length, code_base = word(image,1), word(image,3)
    data_length = word(image,10)
    data = image[128+code_length*16:128+(code_length+data_length)*16]
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
    return names


def check(path, with_confid=None):
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
    # The release N.CMD seeks with 16-bit file offsets, including the header.
    data_file = 128 + code_length * 16
    directory = word(data, 0x0c3e)
    assert data[0x0c3c:0x0c3e] == b'JW', 'Missing N.CMD signature'
    assert directory and data_file + directory + 48 <= 65536, 'N.CMD directory beyond reach'
    sizes = (1, 1, 1, 54, 54, 54, 16, 16, 16, 16, 55, 48, 48, 5, 40, 5, 8, 8, 1, 16, 16)
    ranges = []
    for index, size in enumerate(sizes):
        start = word(data, directory + 2 * index)
        assert start and start + size <= min(len(data), 65536 - data_file), ('Invalid national slot', index)
        ranges.append((start, start + size))
    ranges.sort()
    assert all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])), 'Overlapping national slots'
    assert data[directory+42:directory+48] == bytes(6), 'Unexpected national slots 21-23'
    names = resident_names(image)
    assert {'PIN', 'PCTMP', 'CLOCK'} <= {name.upper().rstrip('0123456789') for name in names}, ('Missing resident processes', names)
    if with_confid is not None:
        expected={'PIN','PCTMP','CLOCK'} | ({'CONFIDD'} if with_confid else set())
        assert {name.upper().rstrip('0123456789') for name in names} == expected, ('Unexpected resident selection', with_confid, names)
    print(f'PASS: system layout, {count} RTM flags and resident-process chain: ' + ', '.join(names))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',nargs='?',type=Path,default=Path('ccpm.sys'))
    parser.add_argument('--confid',type=int,choices=(0,1),default=None)
    args=parser.parse_args()
    check(args.image,args.confid)
