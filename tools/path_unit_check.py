#!/usr/bin/env python3
"""Execute linked PATH instructions against synthetic environment blocks.

NASM is used only for a disposable emu2 driver, never for shipped code.
"""
from pathlib import Path
import re, subprocess, tempfile
R=Path(__file__).resolve().parent.parent
symbols={}; pending=None
for line in (R/'commands/path/path.lst').read_text(errors='replace').splitlines():
 m=re.match(r'^=\s+([A-Za-z_][A-Za-z_0-9]*):',line)
 if m: pending=m[1].lower()
 m=re.match(r'^[= ]([0-9A-F]{4})\s+',line)
 if not m: continue
 if pending: symbols[pending]=int(m[1],16);pending=None
 d=re.search(r'\b([A-Za-z_][A-Za-z_0-9]*)\s+(?:db|dw|rd|rs)\b',line,re.I)
 if d:symbols[d[1].lower()]=int(m[1],16)
S=lambda n:symbols[n]
b=(R/'commands/path/path.cmd').read_bytes(); clen=int.from_bytes(b[1:3],'little')*16
code=bytearray(b[128:128+clen]); data=b[128+clen:]
code[S('pc_char')]=0xc3
entry=len(code);code+=b'\xe8'+((S('path_builtin')-entry-3)&65535).to_bytes(2,'little')+b'\xcb'
cases=[
 ('=MiXeD',b'OTHER=stay\0PATH=old\0\0',b'OTHER=stay\0PATH=MiXeD\0\0',64),
 (' ;',b'PATH=old\0OTHER=stay\0\0',b'OTHER=stay\0PATH=\0\0',64),
 ('=',b'PATH=old\0\0',b'PATH=\0\0',64),
 ('=new',b'path=one\0PATH=two\0PATHX=keep\0\0',b'PATHX=keep\0PATH=new\0\0',64),
 ('=new',b'OTHER=stay\0\0',b'OTHER=stay\0PATH=new\0\0',64),
 ('',b'PATH=old\0\0',None,64),
 ('='+'X'*127,b'\0\0',b'PATH='+b'X'*127+b'\0\0',134),
 ('='+'X'*128,b'PATH=old\0\0',None,256),
 ('=new',b'OTHER=stay\0\0',None,18),
 ('=new',b'X'*64,None,64),
 ('=new',b'PATH=old\0\0',None,1),
 ('=new',b'PATH=old\0\0',None,1025),
 ('=new',b'PATH=old\0\0',None,65535),
]
def db(b):return ','.join(str(v) for v in b)
with tempfile.TemporaryDirectory(prefix='cdos-path-unit-') as t:
 f=Path(t);(f/'code.bin').write_bytes(code);(f/'data.bin').write_bytes(data)
 for i,(text,env,expected,capacity) in enumerate(cases):
  block=env.ljust(max(capacity if capacity<=1024 else 256,256),b'\0')
  wanted=block if expected is None else expected.ljust(len(block),b'\0')
  source=f'''bits 16
cpu 8086
org 100h
 mov ax,cs
 add ax,(production-$$+100h)/16
 mov [target+2],ax
 mov ax,cs
 add ax,(state-$$+100h)/16
 mov ds,ax
 mov es,ax
 mov word [{S('ms_func_jmp_addr')}],query
 mov ax,cs
 mov word [{S('ms_func_jmp_addr')+2}],ax
 mov si,input_text
 mov di,1800h
copy_input:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_input
 mov si,1800h
 call far [cs:target]
 mov ax,cs
 add ax,(environment-$$+100h)/16
 mov es,ax
 xor di,di
 mov si,expected_bytes
 mov cx,{len(block)}
compare:
 mov al,[cs:si]
 cmp al,[es:di]
 jne failed
 inc si
 inc di
 loop compare
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
query:
 mov dx,{capacity}
 mov ax,0ffffh
 cmp dx,65535
 je query_done
 mov ax,cs
 add ax,(environment-$$+100h)/16
query_done:
 retf
target: dw {entry},0
input_text: db {db(text.encode()+bytes([0]))}
expected_bytes: db {db(wanted)}
align 16
production: incbin "code.bin"
align 16
state: incbin "data.bin"
 times 2000h-($-state) db 0
align 16
environment: db {db(block)}
'''
  (f/'test.asm').write_text(source)
  subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=f,check=True,capture_output=True)
  x=subprocess.run(['emu2','test.com'],cwd=f,capture_output=True,timeout=5)
  assert x.returncode==0,(i,text,capacity,x.stdout,x.stderr)
print('PASS: linked PATH update/clear/duplicates/case/127-byte limit/capacity/malformed and unavailable API; errors leave the environment unchanged')
