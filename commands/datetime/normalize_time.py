#!/usr/bin/env python3
"""Normalize LINK86's TIME output to the CDOS 4.11 executable envelope."""

from pathlib import Path
import struct
import sys


LINKED_SIZE = 0xA00
FINAL_SIZE = 0x800


def normalize(path):
    image = bytearray(path.read_bytes())
    if len(image) != LINKED_SIZE or image[:2] != b'MZ':
        raise ValueError(f'{path}: unexpected LINK86 MZ image')

    expected_header = {
        2: 0x200,
        4: 5,
        6: 1,
        8: 0x20,
        10: 0,
        12: 0xffff,
        14: 0x58,
        16: 0x80,
        20: 0x80,
        22: 0,
        24: 0x20,
    }
    for offset, expected in expected_header.items():
        actual = struct.unpack_from('<H', image, offset)[0]
        if actual != expected:
            raise ValueError(
                f'{path}: unexpected MZ header word at {offset:#x}: {actual:#x}'
            )

    if struct.unpack_from('<HH', image, 0x20) != (0x81, 0):
        raise ValueError(f'{path}: unexpected relocation table')
    if image[FINAL_SIZE:] != bytes(LINKED_SIZE - FINAL_SIZE):
        raise ValueError(f'{path}: unexpected nonzero LINK86 trailing data')

    del image[FINAL_SIZE:]
    struct.pack_into('<H', image, 4, 4)
    struct.pack_into('<H', image, 14, 0x53)
    # Preserve the release's checksum field, which is not LINK86's checksum.
    struct.pack_into('<H', image, 18, 0xd4bb)
    path.write_bytes(image)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: normalize_time.py TIME.EXE')
    normalize(Path(sys.argv[1]))
