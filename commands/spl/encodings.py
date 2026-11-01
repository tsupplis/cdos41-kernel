"""Restore the 4.11 linker's DATA maximum and alternate register encodings."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
image = bytearray(path.read_bytes())
if len(image) != 12160 or image[:18] != bytes.fromhex('01e3010000e3010000020701000007010000'):
    raise ValueError('Unexpected GENCMD group descriptors')
image[16:18] = bytes.fromhex('2201')  # DATA maximum is 0122h paragraphs.
encodings = [
    ("8bf0", "89c6", [0x937, 0x1093]),  # mov si,ax
    ("8bf8", "89c7", [0x94a, 0xd07, 0x119a, 0x17dd, 0x18e7]),  # mov di,ax
]
for assembled, original, sites in encodings:
    for site in sites:
        start = 128 + site
        if image[start:start + 2] != bytes.fromhex(assembled):
            raise ValueError(f'Unexpected instruction at CODE {site:04X}')
        image[start:start + 2] = bytes.fromhex(original)
path.write_bytes(image)
