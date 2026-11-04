"""Check the 4.11 DSKMAINT assembly modules and constants against the release."""
from pathlib import Path
import hashlib
import re


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

# SQUIDDM3 now intentionally extends the format/menu implementation. Keep
# independent release checks on unchanged compiled components, locating them
# through the link map instead of assuming their historical offsets.
maptext=Path('dskraw.map').read_text(errors='replace')
def module_range(name,section):
    block=maptext.split('map for module:  '+name)[1].split('map for module:')[0]
    m=re.search(r'([0-9A-F]+)  \(0000:([0-9A-F]+)-[0-9A-F]+\)\s+'+section,block)
    return int(m[2],16),int(m[1],16)
fcode,flen=module_range('FUNC10','CODE')
fdata,fdlen=module_range('FUNC10','DATA')
assert flen==0x273 and fdlen==0x1f
relocated(old_code[0x1cea:0x1f5d],code[fcode:fcode+flen],0x3228-fdata,31)
helpdata,helplen=module_range('HELP','DATA')
assert old_data[0x2ccc:0x2ccc+helplen]==data[helpdata:helpdata+helplen]
const,constlen=module_range('HELP','CONST')
assert constlen==0x20c and old_data[0x236:0x442]==data[const:const+constlen]
assert old_data[0x3228:0x3247]==data[fdata:fdata+fdlen]
print('PASS: unchanged FUNC10, HELP data and constants retain checked 4.11 equivalence; extended format/menu code is checked separately')
