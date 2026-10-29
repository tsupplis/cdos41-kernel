#!/usr/bin/env python3
"""Preserve the OEM MZ stack/checksum words; never modify executable code/data."""
from pathlib import Path
import struct
p=Path('ren.exe')
b=bytearray(p.read_bytes())
assert len(b)==2048 and b[:2]==b'MZ', 'Unexpected LINK86 image'
assert struct.unpack_from('<H',b,14)[0]==0x40, 'Unexpected linker stack placement'
assert sum(struct.unpack('<1024H',b))&0xffff==0, 'Invalid linker checksum'
# OEM puts the 128-byte stack at paragraph 3Eh, immediately after rounded DATA.
# LINK86 2.02 uses 40h. Both locations are in the zero-filled file tail.
assert not any(b[512+0x3e0:512+0x480]), 'Stack reserve is not zero-filled'
struct.pack_into('<H',b,14,0x3e)
# Historical checksum is stale (whole-file word sum 7727h); preserve, don't fix.
struct.pack_into('<H',b,18,0x4ed3)
p.write_bytes(b)
