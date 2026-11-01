#!/usr/bin/env python3
"""4.11 whole-image equivalence and isolated command-tail regression cases."""
from pathlib import Path
import hashlib
import struct
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from pctmp_recovery_check import near
from fat_recovery_check import hook

REFERENCE_SHA256 = '29d0917a45cea17040dea5ba991ce706db3876f0ced13724bb687551bb4ddf5b'


def check():
    original = (ROOT / '../../base/copy.exe').read_bytes()
    actual = (ROOT / 'copy.exe').read_bytes()
    assert hashlib.sha256(original).hexdigest() == REFERENCE_SHA256, '4.11 reference changed'
    assert len(original) == 29184
    # Only source serial text, LINK86 stack placement and its checksum differ.
    expected = bytearray(original)
    assert expected[0x22b:0x23b] == b'1031-0000       '
    expected[0x22b:0x23b] = b'XXXX-0000-654321'
    assert struct.unpack_from('<H', expected, 14)[0] == 0x6e6
    assert not any(expected[0x7060:0x7100]), 'Stack reserve is not zero-filled'
    struct.pack_into('<H', expected, 14, 0x6e8)
    struct.pack_into('<H', expected, 18, 0)
    checksum = (-sum(struct.unpack('<14592H', expected))) & 0xffff
    struct.pack_into('<H', expected, 18, checksum)
    assert actual == expected, 'Unexpected COPY byte difference'
    print('PASS: complete COPY matches 4.11 with only exact serial/SS/checksum differences')

    cases = ['', 'A.TXT B.TXT', 'A.TXT+B.TXT C.TXT',
             'A.TXT+B.TXT+C.TXT D.TXT', 'N:A.TXT O:B.TXT /V',
             'C:\\A.TXT B.TXT', 'A.TXT D:\\B.TXT',
             '\\DIR\\A.TXT B.TXT', 'A.TXT+B:\\C.TXT D.TXT']
    count = 0
    for image in (original, actual):
        for text in cases:
            code = bytearray(image[512:])
            # Stop after tail preparation. Stub only output and direct exit;
            # reject any accidental route through file-deleting cleanup.
            code[0xab] = 0xc3
            hook(code, 0x803, 'mov byte [es:0f000h],1\nret')
            hook(code, 0x363, 'mov byte [es:0f001h],1\nret')
            hook(code, 0x342, 'mov byte [es:0f002h],1\nret')
            raw = (text + '\r').encode().ljust(128, b'\0')
            rejected = '\\' in text
            body = '''add ax,1000h
 mov es,ax
 mov bx,ax
 add ax,1000h
 mov ds,ax
 mov si,0f100h
 mov di,0f100h
 mov cx,128
 mov dl,'+'
 mov al,' '
 mov word [es:0f000h],0
 mov byte [es:0f002h],0
 mov byte [es:266h],0
'''
            body += '\n'.join(f'mov byte [0f100h+{i}],{v}' for i,v in enumerate(raw))
            body += f'''\ncall far [cs:target]
 cmp byte [es:0f000h],{int(rejected)}
 jne failed
 cmp byte [es:0f001h],{int(rejected)}
 jne failed
 cmp byte [es:0f002h],0
 jne failed
'''
            if not rejected:
                output = raw.replace(b'+', b' +')
                body += f'cmp byte [es:266h],{255 if "+" in text else 0}\njne failed\n'
                for i,v in enumerate(output):
                    body += f'cmp byte [es:0f100h+{i}],{v}\njne failed\n'
            near(code, 0x9d, body)
            count += 1
    print(f'PASS: {count} original/rebuilt tail cases: filenames, concatenation, floating drives, /V, path rejection and no deletion cleanup (I/O stubbed)')


if __name__ == '__main__':
    check()
