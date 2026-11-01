"""Check the 4.11 DSKMAINT assembly modules and constants against the release."""
from pathlib import Path
import hashlib


def groups(image):
    code_size = int.from_bytes(image[1:3], 'little') * 16
    data_size = int.from_bytes(image[10:12], 'little') * 16
    return image[128:128+code_size], image[128+code_size:128+code_size+data_size]


def relocated(original, rebuilt, delta, count):
    """Every differing word must have the same documented address adjustment."""
    assert len(original) == len(rebuilt)
    offset = 0
    changes = 0
    while offset < len(original):
        if original[offset] == rebuilt[offset]:
            offset += 1
            continue
        assert offset+2 <= len(original)
        old = int.from_bytes(original[offset:offset+2], 'little')
        new = int.from_bytes(rebuilt[offset:offset+2], 'little')
        assert old == new + delta, (hex(offset), hex(old), hex(new))
        changes += 1
        offset += 2
    assert changes == count, (changes,count)


original = Path('../../base/dskmaint.cmd').read_bytes()
assert hashlib.sha256(original).hexdigest() == 'e70332946f5325d7a85b31accf4dec8361f07610a91f61fc60aa3326e4c3c3b8'
old_code, old_data = groups(original)
code, data = groups(Path('dskmaint.cmd').read_bytes())

# Offsets from DSKRAW.MAP. The release places CONST (020Ch bytes) before
# the application DATA group. Its compiled HELP body is 0078h bytes longer.
relocated(old_code[:0xd84], code[:0xd84], 0x20c, 316)
relocated(old_code[0xd90:0xe76], code[0xd90:0xe76], 0x78, 1)
relocated(old_code[0x1cea:0x1f5d], code[0x1c72:0x1ee5], 0x20c, 31)
assert old_data[:0x236] == data[:0x236]
assert old_data[0x236:0x442] == data[0x303c:0x3248]
relocated(old_data[0x442:0x2ccc], data[0x236:0x2ac0], 0x20c, 140)
assert old_data[0x2ccc:0x3228] == data[0x2ac0:0x301c]
assert old_data[0x3228:0x3247] == data[0x301c:0x303b]
print('PASS: assembly modules, FUNC10, startup, embedded loader, HELP data and constants match after checked relocations')
