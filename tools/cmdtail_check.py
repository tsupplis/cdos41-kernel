#!/usr/bin/env python3
"""Execute the assembled CMD tail loop and verify one-byte header edits."""
from pathlib import Path
from historical_check import symbols, payload, run

ROOT=Path(__file__).resolve().parent.parent

def check():
    for name in ['putget/put', 'putget/get', 'putget/rdr', 'echo/echo', 'batch/batch', 'setenv/setenv', 'path/path']:
        assert (ROOT/f'commands/{name}.cmd').read_bytes()[127]&2,name
    s=symbols('sup');code=payload('sup')
    # Complete the tail loop with its normal length store and a test return.
    # No mocked case-conversion instructions: execute production NCMDCHAR.
    code[s['ENDTAIL']:s['ENDTAIL']+5]=b'\x88\x0e\x80\x00\xcb'
    run(code,s['NCMDCHAR'],'''
 xor bp,bp
next_flags:
 mov di,0f100h
 mov cx,127
 mov al,1
fill:
 stosb
 inc al
 loop fill
 mov byte [di],0
 mov ax,bp
 mov ch,al
 xor cl,cl
 mov di,0f100h
 call far [cs:target]
 cmp byte [80h],127
 jne failed
 cmp byte [0f17fh],0
 jne failed
 mov di,0f100h
 mov si,1
verify:
 mov ax,si
 test bp,2
 jnz compare
 cmp al,'a'
 jb compare
 cmp al,'z'
 ja compare
 and al,05fh
compare:
 cmp al,[di]
 jne failed
 inc di
 inc si
 cmp si,128
 jb verify
 inc bp
 cmp bp,256
 jb next_flags
''')
    print('PASS: CMD KEEP flags; 256 header-flag combinations x 127 non-NUL bytes through assembled CLI code')

if __name__=='__main__':check()
