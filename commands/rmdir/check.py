#!/usr/bin/env python3
"""Check all RMDIR bytes against 4.11 and execute extended-error mappings."""
from pathlib import Path
import hashlib
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from pctmp_recovery_check import near

def check():
    old = (ROOT / '../../base/rmdir.cmd').read_bytes()
    new = (ROOT / 'rmdir.cmd').read_bytes()
    assert hashlib.sha256(old).hexdigest() == '2385e819a48878e65034af0cd2ecfa2361ba0ddca7eb5dc18851fa6f95450086'
    assert len(old) == len(new) == 2176
    assert old[:128] == new[:128]
    assert new[128:190] == HEADER
    assert old[128+0x30:128+0x4b2] == new[128+0x3e:128+0x4c0]
    assert not any(old[128+0x4b2:128+0x4c0])
    assert old[1344:] == new[1344:]
    print('PASS: complete RMDIR code/data match 4.11 after copyright/entry relocation')
    for image, entry in ((old, 0x441), (new, 0x44f)):
        code = bytearray(image[128:1344])
        data = image[1344:]
        for error, result, message in [(1,3,'Physical disk error'),
                (2,6,'Read only disk'), (3,9,"Subdirectory set to Read Only - Can't remove"),
                (8,7,'Directory already exists'), (9,2,'Invalid path'),
                (10,5,"Can't change directory")]:
            body = 'add ax,1000h\nmov ds,ax\nmov es,ax\n'
            body += '\n'.join(f'mov byte [{i}],{b}' for i,b in enumerate(data))
            body += f'\nmov ax,{error<<8}\ncall far [cs:target]\ncmp al,{result}\njne failed\nmov si,dx\n'
            for b in message.encode()+b'\0':
                body += f'lodsb\ncmp al,{b}\njne failed\n'
            near(code, entry, body)
    print('PASS: 12 original/rebuilt extended-error cases including read-only directory')

HEADER = bytes.fromhex('e93b00434f5059524947485428632920313938352c20494e54455247414c4143544943204449474954414c205245534541524348202030322f32392f3835')
if __name__ == '__main__':
    check()
