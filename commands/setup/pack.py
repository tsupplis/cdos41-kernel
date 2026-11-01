"""Finish the 4.11 CMD after ASM86 and GENCMD, without reading a reference CMD."""
from pathlib import Path
import sys

# CODE, DATA and STACK are paragraph counts. The linker permits DATA to grow
# to 1000h paragraphs and places its relocation list in disk record 7Eh.
CODE = bytes.fromhex('01 c701 0000 c701 0000')
DATA = bytes.fromhex('02 1e02 0000 1e02 0000')
STACK = bytes.fromhex('04 0300 0000 0300 0000')
END_GROUPS = 0x3f00

# ASM86 encoding, release encoding and CODE offsets. All pairs have equal
# length and execute the mnemonic shown beside the entry.
ENCODINGS = [
    # mov al,ah
    ("8ac4", "88e0", [
        0xe54,
    ]),
    # mov si,cx
    ("8bf1", "89ce", [
        0xebe,
    ]),
    # cmp ax,0x3f
    ("3d3f00", "83f83f", [
        0xf9c,
    ]),
    # xor dx,dx
    ("33d2", "31d2", [
        0xfe4, 0x14e6,
    ]),
    # mov bx,ax
    ("8bd8", "89c3", [
        0xfea, 0x1126, 0x11b0, 0x1279, 0x12be, 0x12d6, 0x131b, 0x1339,
        0x1355, 0x1365, 0x1381, 0x140e, 0x1424, 0x149e, 0x152c, 0x154f,
        0x15c6, 0x15e4, 0x15f0, 0x1604, 0x162c, 0x164f, 0x1697, 0x16a5,
        0x16d6, 0x1713, 0x174d, 0x1766, 0x1782, 0x17a1, 0x180b,
    ]),
    # mov cx,ax
    ("8bc8", "89c1", [
        0x11a9,
    ]),
    # mov si,dx
    ("8bf2", "89d6", [
        0x127d,
    ]),
    # mov si,ax
    ("8bf0", "89c6", [
        0x1670,
    ]),
]

def finish(path):
    image = bytearray(path.read_bytes())
    generated = CODE + DATA + bytes(9) + STACK + bytes(92)
    if image[:128] != generated or image[END_GROUPS:] != bytes(128):
        raise ValueError(f"{path}: unexpected GENCMD layout")
    for assembled, original, offsets in ENCODINGS:
        before, after = bytes.fromhex(assembled), bytes.fromhex(original)
        for offset in offsets:
            start = 128 + offset
            if image[start:start + len(before)] != before:
                raise ValueError(f"{path}: unexpected instruction at CODE {offset:04X}")
            image[start:start + len(before)] = after

    # The loader adds the DATA segment to HELP's two MOV AX,0 immediates.
    relocation_record = bytearray()
    for offset in (0x0b03, 0x0b10):
        if image[128 + offset - 1:128 + offset + 2] != bytes.fromhex('b8 0000'):
            raise ValueError(f"{path}: unexpected relocation target at {offset:04X}")
        relocation_record.append(0x12)  # word in CODE referencing DATA
        relocation_record.extend((offset >> 4).to_bytes(2, 'little'))
        relocation_record.append(offset & 15)
    image[END_GROUPS:] = relocation_record.ljust(128, bytes(1))
    image[:128] = CODE + DATA[:-2] + bytes.fromhex('0010') + STACK + bytes(98) + bytes.fromhex('7e0080')
    path.write_bytes(image)


if __name__ == '__main__':
    finish(Path(sys.argv[1]))
