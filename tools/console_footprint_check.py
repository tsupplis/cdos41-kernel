#!/usr/bin/env python3
"""Check configured console allocations and exercise built CIO recall bounds.

Default: four PC consoles, no resident serial-terminal shells. The optional
OEM terminal profile adds two consoles. UART AUX/printer support stays at two.
Budgets cover the standard generated system; raising one requires reviewing
and documenting the resident footprint rather than accepting silent growth.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CON = ROOT/'kernel/con'

def symbols(name):
    return {n: int(v,16) for v,n in re.findall(r'\b([0-9A-F]{4})\s+([A-Z][A-Z0-9]*)', (CON/(name+'.sym')).read_text())}

def payload(name):
    b = (CON/(name+'.con')).read_bytes()
    return b[128:128+int.from_bytes(b[1:3],'little')*16]

s = symbols('squid')
c = symbols('cio')
virtual, serial = s['NUMVIRCONS'], s['NUMSERIALCONS']
policy=(CON/'consoles.def').read_text()
assert serial == int(re.search(r'num_serial_cons\s+equ\s+(\d+)',policy).group(1)), 'Stale XIOS console policy'
assert virtual == 4 and serial in (0,2), 'Unsupported console configuration'
consoles, physical = virtual+serial, 1+serial
x = payload('xios')
assert x[s['NVCNS']] == x[s['NCCB']] == consoles
assert x[s['NPCNS']] == physical
assert x[s['NACB']] == s['NUMAUXPORTS'] == 2, 'UART AUX support changed'
assert c['RECALLSLOTS'] == consoles
assert c['RAWINIT']-c['RECALLLINES'] == 256*consoles
image = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'kernel/sysgen/ccpm.sys'
b = image.read_bytes()
w = lambda b,o: int.from_bytes(b[o:o+2],'little')
base, code = w(b,3), w(b,1)
d = b[128+code*16:]
assert d[0x47] == d[0x49] == consoles
segment = w(d,0x42)
names = []
while segment:
    at = 128+(segment-base)*16
    assert 128 <= at < len(b)-64
    h = b[at:at+64]
    names.append(h[24:32].decode('ascii').strip().upper())
    assert len(names)<32, 'Circular resident chain'
    segment = w(h,0)
assert len([n for n in names if n.startswith('PCTMP')]) == consoles
assert len([n for n in names if n.startswith('PIN')]) == physical
assert {n for n in names if n.startswith('PCTMP')} == {f'PCTMP{i}' for i in range(consoles)}, names
assert {n for n in names if n.startswith('PIN')} == {f'PIN{i}' for i in range(physical)}, names
# Every configured DPH must share the same reviewed pool. GENCCPM's '*:'
# duplicates numeric settings; sharing requires a named A: pool followed by
# '*:' with A: as the directory/data source.
headers = set()
for drive in range(16):
    dph = w(d,0x0c18+2*drive)
    if dph:
        headers.add((w(d,dph+14),w(d,dph+16)))
assert len(headers)==1, f'Per-drive buffer duplication: {headers}'
recipe=[line.strip().lower() for line in (ROOT/'kernel/sysgen/genccpm.in').read_text().splitlines()]
setting=recipe.index('diskbuffers')
assert recipe[setting+1]=='a:', 'Expected named A: buffer pool'
dir_count,dir_limit,data_count,data_limit=(int(v,16) for v in recipe[setting+2:setting+6])
assert 0<dir_limit<=dir_count<=127 and 0<data_limit<=data_count<=127
assert recipe[setting+6:setting+10]==['*:', 'a:', 'a:', 'no'], 'Other drives must share A:'
dir_header,data_header = headers.pop()
for header,total,per_process in [(dir_header,dir_count,dir_limit),(data_header,data_count,data_limit)]:
    seen=set()
    item=w(d,header)
    while item:
        assert item not in seen and item+16<=len(d), 'Invalid buffer chain'
        seen.add(item)
        item=w(d,item+12)
    assert len(seen)==total, (len(seen),total)
    assert d[header+2]==per_process
budget = (166 if serial==0 else 182)*1024
assert len(b) <= budget, f'System footprint {len(b)} exceeds reviewed {budget}-byte budget'

# Call the production recall-slot selector for every possible byte console ID.
# The stub only supplies the far entry/return required by the DOS test driver.
code = bytearray(payload('cio'))
code[:4] = b'\xe8'+((c['RECALLSLOT']-3)&65535).to_bytes(2,'little')+b'\xcb'
with tempfile.TemporaryDirectory(prefix='cdos-console-bounds-') as td:
    p = Path(td)
    (p/'cio.bin').write_bytes(code)
    (p/'test.asm').write_text(f'''bits 16
cpu 8086
org 100h
 mov ax,cs
 add ax,(payload-$$+100h)/16
 mov [target+2],ax
 mov ds,ax
 xor si,si
next:
 mov dx,si
 mov dh,dl
 call far [cs:target]
 pushf
 pop bx
 cmp si,{consoles}
 jb valid
 test bx,1
 jz failed
 jmp done
valid:
 test bx,1
 jnz failed
 mov ax,si
 mov cl,8
 shl ax,cl
 add ax,{c['RECALLLINES']}
 cmp di,ax
 jne failed
done:
 inc si
 cmp si,256
 jb next
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
target dw 0,0
align 16
payload: incbin "cio.bin"
''')
    subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=p,check=True,capture_output=True)
    result = subprocess.run(['emu2','test.com'],cwd=p,timeout=10,capture_output=True)
    assert result.returncode==0, (result.stdout,result.stderr)
print(f'PASS: all configured drives share {dir_count} directory/{data_count} data buffers; per-process limits {dir_limit}/{data_limit}')
print(f'PASS: {consoles} consoles, {physical} PIN, two UART AUX ports, {consoles*256} recall bytes, 256 recall bounds; SYS {len(b)} bytes (budget {budget})')
# Execute the production UART-startup policy with only hardware boundaries
# stubbed. An unused/missing serial terminal must not consume an AUX port.
for port in (0,1):
    for present in (False,True):
        for requested in (False,True):
            native = bytearray(x)
            stubs = {
                'POINTAUX': bytes.fromhex('31db c3'),
                'AUXPORTIN': bytes([0xb0,0 if present else 0xf8,0xc3]),
                'DOAUXINT': bytes.fromhex('fe0600f0 c3'),
                'ERASEPORT': bytes.fromhex('fe0601f0 c3'),
                'SETSERCON': bytes.fromhex('fe0602f0 c3'),
            }
            for name,stub in stubs.items():
                at,dest=s[name],len(native)
                native.extend(stub)
                native[at:at+3]=b'\xe9'+((dest-at-3)&65535).to_bytes(2,'little')
            native[:4]=b'\xe8'+((s['DOONEPORT']-3)&65535).to_bytes(2,'little')+b'\xcb'
            terminal=present and requested and port<serial
            erased=(not present) or terminal
            with tempfile.TemporaryDirectory(prefix='cdos-uart-policy-') as td:
                p=Path(td)
                (p/'xios.bin').write_bytes(native)
                (p/'test.asm').write_text(f'''bits 16
cpu 8086
org 100h
 mov ax,cs
 add ax,(payload-$$+100h)/16
 mov [target+2],ax
 mov ds,ax
 mov word [0f000h],0
 mov byte [0f002h],0
 mov byte [{s['SUSERCON']+port}],{255 if requested else 0}
 mov dx,{port}
 mov cl,0ffh
 call far [cs:target]
 cmp byte [0f000h],{int(present)}
 jne failed
 cmp byte [0f001h],{int(erased)}
 jne failed
 cmp byte [0f002h],{int(terminal)}
 jne failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
target dw 0,0
align 16
payload: incbin "xios.bin"
''')
                subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=p,check=True,capture_output=True)
                result=subprocess.run(['emu2','test.com'],cwd=p,timeout=10,capture_output=True)
                assert result.returncode==0,(port,present,requested,result.stdout,result.stderr)
print('PASS: eight assembled UART startup policies; AUX stays available unless a configured terminal claims its port')
