#!/usr/bin/env python3
"""Compare INITDIR with 4.11, permitting only its overwritten runtime word."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent
# Pin the independently extracted 4.11 image, not a rebuilt reference.
REFERENCE_SHA256 = 'e8b36210b48f0abdb400ab9a9e5f8577fb546b48033fbd5ff764add6bd9a2a1d'

def check():
    original = (ROOT / '../../base/initdir.cmd').read_bytes()
    actual = (ROOT / 'initdir.cmd').read_bytes()
    assert hashlib.sha256(original).hexdigest() == REFERENCE_SHA256, '4.11 reference changed'
    assert len(original) == 36992
    code_size = int.from_bytes(original[1:3], 'little') * 16
    data_start = 128 + code_size
    offset = data_start + 0x3c25
    assert offset == 0x8a55 and original[offset:offset+2] == b'\0\0'
    # The first procedure calls runtime initialization, which writes this
    # stack-limit word before installing SS:SP and returning to INITDIR.
    assert original[128:139] == bytes.fromhex('e902009090bb0002e8ad1e')
    assert original[128+0x1ee3:128+0x1ef4] == bytes.fromhex('a1323c0500047223a3253c8cdb8ed38be0')
    expected = bytearray(original)
    expected[offset:offset+2] = b'\xff\xff'
    assert actual in (original, bytes(expected)), 'Unexpected INITDIR byte difference'
    print('PASS: complete INITDIR matches 4.11 except optional 0000/FFFF runtime word at 8A55h; all code, headers and other data identical')

if __name__ == '__main__':
    check()
