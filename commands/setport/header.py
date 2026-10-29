"""Restore SETPORT's CMD descriptors and unloaded relocation record.

GENCMD leaves an empty EXTRA descriptor before STACK. No group payload is
changed here. The final disk record contains two loader relocations, a zero
terminator, and historical linker-buffer residue that is never loaded.
"""
from pathlib import Path
import sys

HEADER = bytes.fromhex(
    '01cc010000cc010000027802000078020000041300000013000000'
) + bytes(98) + bytes.fromhex('8c0080')
TRAILER = bytes.fromhex(
    '12b5000312b6000000'
    'bee00d0336dc0d8a04bfa10ee80100c3b90300d0d8bbe80e7203bbed0e891d83c716'
    'e2efc3b90300b00ee83800061e8cd88ec08e1ecd11b90400bfde0d8b37a44343e2f9'
    '1f07c3b90300b80e00e81500068e06cd11b90400bede0d268b3fa44343e2f807c31e'
    '068e1ecd118e06d111ff1e2800071fc3bb'
)

def normalize(path):
    image = path.read_bytes()
    expected_header = HEADER[:18] + bytes(9) + HEADER[18:27] + bytes(92)
    if len(image) != 17920 or image[:128] != expected_header:
        raise SystemExit(f'{path}: unexpected GENCMD group layout/header')
    if image[17904:] != bytes(16):
        raise SystemExit(f'{path}: unexpected end-of-groups padding')
    if image[128+0xb53:128+0xb55] != bytes(2) or image[128+0xb60:128+0xb62] != bytes(2):
        raise SystemExit(f'{path}: DATA relocation words are not zero')
    assert len(HEADER) == len(TRAILER) == 128
    path.write_bytes(HEADER + image[128:] + TRAILER)

if __name__ == '__main__':
    normalize(Path(sys.argv[1]))
