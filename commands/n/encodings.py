"""Restore the 4.11 linker's DATA maximum and alternate register encodings."""
from pathlib import Path

path = Path('norg.cmd')
image = bytearray(path.read_bytes())
if len(image) != 8704 or image[:18] != bytes.fromhex('01b6010000b6010000025c0000005c000000'):
    raise ValueError('Unexpected GENCMD group descriptors')
image[17] = 0x10  # DATA may grow to 1000h paragraphs.
encodings = [
    ("8bf0", "89c6", [0x1658, 0x1682, 0x16bb, 0x16d2, 0x16e4, 0x176f, 0x178d, 0x17c1]),  # mov si,ax
    ("8bf8", "89c7", [0x1660, 0x167e, 0x170a, 0x17e5, 0x1807, 0x18e3]),  # mov di,ax
    ("8bfe", "89f7", [0x16ce, 0x178f]),  # mov di,si
    ("3bf0", "39c6", [0x17ef, 0x17fb]),  # cmp si,ax
    ("3bf8", "39c7", [0x17f5]),  # cmp di,ax
    ("03f8", "01c7", [0x190a]),  # add di,ax
    ("03f0", "01c6", [0x190f]),  # add si,ax
]
for assembled, original, sites in encodings:
    for site in sites:
        start = 128 + site
        if image[start:start + 2] != bytes.fromhex(assembled):
            raise ValueError(f'Unexpected instruction at CODE {site:04X}')
        image[start:start + 2] = bytes.fromhex(original)
path.write_bytes(image)
