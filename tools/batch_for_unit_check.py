#!/usr/bin/env python3
"""Run production BATCH expansion/FOR bytes under a disposable test driver.

OS queries and diagnostics alone are stubbed. File enumeration is exercised
separately on native CP/M/FAT media by batch_for_check.py.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
symbols={}
pending=None
for line in (ROOT/'commands/batch/batch.lst').read_text(errors='replace').splitlines():
    label=re.match(r'^=\s+([A-Za-z_][A-Za-z_0-9]*):',line)
    if label: pending=label[1].upper()
    address=re.match(r'^=([0-9A-F]{4})\s+',line)
    if address:
        if pending:
            symbols[pending]=int(address[1],16);pending=None
        decl=re.search(r'\b([A-Za-z_][A-Za-z_0-9]*)\s+(?:db|dw|dd|rb|rs|rw|rd)\b',line,re.I)
        if decl: symbols[decl[1].upper()]=int(address[1],16)+0x100
S=lambda n:symbols[n.upper()]
cmd=(ROOT/'commands/batch/batch.cmd').read_bytes()
size=int.from_bytes(cmd[1:3],'little')*16
code=bytearray(cmd[128:128+size])
data=bytes(256)+cmd[128+size:128+size+int.from_bytes(cmd[10:12],'little')*16]
code[S('print_string'):S('print_string')+5]=b'\xfe\x06\x01\xf0\xc3'
code[S('crlf')]=0xc3
code[S('condition_probe'):S('condition_probe')+6]=b'\xc6\x06'+S('condition_error').to_bytes(2,'little')+b'\x01\xc3'
entries={}
for name in ['batch_expand','batch_for','for_next','batch_condition','for_collect_file']:
    entries[name]=len(code)
    code+=b'\xe8'+((S(name)-len(code)-3)&65535).to_bytes(2,'little')+b'\xcb'
cases=[
 ('FOR %%I IN (A, B, "%VAL%", "AA AA") DO ECHO %%I',['ECHO A','ECHO B','ECHO "Mixed Value"','ECHO "AA AA"']),
 ('for %%i in (a b,c) do ECHO %%i',['ECHO a','ECHO b','ECHO c']),
 ('FOR %%I IN ("A,B", "A)B", "", A" B") DO ECHO %%I',['ECHO "A,B"','ECHO "A)B"','ECHO ""','ECHO A" B"']),
 ('FOR %%I IN () DO ECHO %%I',[]),
 ('FOR %%I IN (, ,) DO ECHO %%I',[]),
 ('FOR %%I IN (1..3) DO ECHO %%I',['ECHO 1','ECHO 2','ECHO 3']),
 ('FOR %%I IN (3..1) DO ECHO %%I',['ECHO 3','ECHO 2','ECHO 1']),
 ('FOR %%I IN (-2..2) DO ECHO %%I',[f'ECHO {n}' for n in range(-2,3)]),
 ('FOR %%I IN (+2..-1) DO ECHO %%I',[f'ECHO {n}' for n in range(2,-2,-1)]),
 ('FOR %%I IN (32766..32767) DO ECHO %%I',['ECHO 32766','ECHO 32767']),
 ('FOR %%I IN (-32767..-32768) DO ECHO %%I',['ECHO -32767','ECHO -32768']),
 ('FOR %%I IN (0..0) DO ECHO %%I',['ECHO 0']),
 ('FOR %%I IN (-0..+0) DO ECHO %%I',['ECHO 0']),
 ('FOR %%I IN (001..002) DO ECHO %%I',['ECHO 1','ECHO 2']),
 ('FOR %%I IN ("1..3") DO ECHO %%I',['ECHO "1..3"']),
 ('FOR %%I IN (1..3 X) DO ECHO %%I',['ECHO 1..3','ECHO X']),
 ('FOR %%I IN (A..B) DO ECHO %%I',['ECHO A..B']),
 ('FOR %%I IN (32768) DO ECHO %%I',['ECHO 32768']),
 ('FOR %%I IN ("FILES") DO ECHO %%I',['ECHO "FILES"']),
 ('FOR %%I IN (FILES) DO ECHO %%I',['ECHO FILES']),
 ('FOR %%I IN (A) DO ECHO %%I/%%I/%%i',['ECHO A/A/%i']),
 ('FOR %%I IN (%%OTHER%%) DO ECHO %%I',['ECHO %OTHER%']),
 ('FOR %%I IN (A) DO IF "%%I"=="A" ECHO %%I',['IF "A"=="A" ECHO A']),
]
for source in ['FOR','FOR %%1 IN (A) DO ECHO x','FOR %%AB IN (A) DO ECHO x',
               'FOR %%I ON (A) DO ECHO x','FOR %%I IN A DO ECHO x',
               'FOR %%I IN (A) ECHO x','FOR %%I IN (A) DO',
               'FOR %%I IN ("A) DO ECHO x','FOR %%I IN ((A)) DO ECHO x',
               'FOR %%I IN (32768..1) DO ECHO x','FOR %%I IN (-32769..1) DO ECHO x',
               'FOR %%I IN (1..99999999999999) DO ECHO x','FOR %%I IN (1..x) DO ECHO x',
               'FOR %%I IN (FILES B:*.C extra) DO ECHO x',
               'FOR %%I IN (FILES B:*.C) DO ECHO x']:
    cases.append((source,None))
# Empty expansion provenance must survive the body being saved and rendered.
cases.append(('FOR %%I IN (A) DO IF VALUE==%MISSING% ECHO wrong',['IF VALUE== ECHO wrong'],'ERROR'))
cases.append(('FOR %%I IN ("A""B") DO ECHO %%I',['ECHO "A""B"']))
cases.append(('FOR %%I IN ('+'x'*60+') DO ECHO '+'%%I'*10,[],'OVERFLOW'))

def db(s): return ','.join(str(c) for c in s.encode('latin1')+b'\0')
with tempfile.TemporaryDirectory(prefix='cdos-for-unit-') as name:
    folder=Path(name);(folder/'code.bin').write_bytes(code);(folder/'data.bin').write_bytes(data)
    for number,case in enumerate(cases):
        source,expected=case[:2];special=case[2] if len(case)>2 else None
        assert len(source)<=127,(number,len(source))
        body=f'''bits 16
cpu 8086
org 100h
 cld
 mov ax,cs
 add ax,(production-$$+100h)/16
'''
        for key in entries: body+=f' mov [target_{key}+2],ax\n'
        body+=f''' mov ax,cs
 add ax,(state-$$+100h)/16
 mov ds,ax
 mov es,ax
 mov byte [0f001h],0
 mov byte [{S('for_kind')}],0
 mov word [{S('subparms')}],0
 mov word [{S('ms_func_jmp_addr')}],query
 mov ax,cs
 mov word [{S('ms_func_jmp_addr')+2}],ax
 mov byte [{S('read_blen')}],{len(source)+1}
 mov si,input_line
 mov di,{S('clicb_cmd')}
copy_input:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_input
 call far [cs:target_batch_expand]
 jc failed
 call far [cs:target_batch_for]
 jnc failed
 cmp byte [0f001h],{int(expected is None)}
 jne failed
'''
        for index,result in enumerate(expected or []):
            body+=f''' call far [cs:target_for_next]
 jc failed
 mov si,result_{index}
 mov di,{S('clicb_cmd')}
compare_{index}:
 mov al,[cs:si]
 inc si
 cmp al,[di]
 jne failed
 inc di
 or al,al
 jnz compare_{index}
 cmp byte [{S('read_blen')}],{len(result)+1}
 jne failed
'''
            if special=='ERROR':
                body+=' call far [cs:target_batch_condition]\n jnc failed\n cmp byte [0f001h],1\n jne failed\n'
        body+=f''' call far [cs:target_for_next]
 jnc failed
 cmp byte [{S('for_kind')}],0
 jne failed
 cmp byte [0f001h],{int(expected is None or special is not None)}
 jne failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
query:
 cmp cl,10
 jne failed
 mov ax,cs
 add ax,(environment-$$+100h)/16
 mov dx,17
 retf
'''
        for key,entry in entries.items():body+=f'target_{key} dw {entry},0\n'
        body+=f'input_line db {db(source)}\n'
        for index,result in enumerate(expected or []):body+=f'result_{index} db {db(result)}\n'
        body+='align 16\nproduction: incbin "code.bin"\nalign 16\nstate: incbin "data.bin"\nalign 16\nenvironment db "VAL=Mixed Value",0,0\n'
        (folder/'test.asm').write_text(body)
        subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=folder,check=True,capture_output=True)
        result=subprocess.run(['emu2','test.com'],cwd=folder,capture_output=True,timeout=5)
        assert result.returncode==0,(number,case,result.stdout,result.stderr)
# Exercise the actual snapshot callback at its memory limits, without BDOS.
collector_cases=[
    ('B:\\SUB\\',b'A       COM',False,False),
    ('',b'A       '+bytes([0xa0,0xa0,0xa0]),False,False),
    ('B:'+'A'*124,b'LONGNAMECOM',False,False),
    ('B:',b'A       COM',True,False),
    ('B:',b'A       COM',False,True),
]
with tempfile.TemporaryDirectory(prefix='cdos-for-collector-') as name:
    folder=Path(name);(folder/'code.bin').write_bytes(code);(folder/'data.bin').write_bytes(data)
    for prefix,entry,exact,overflow in collector_cases:
        basename=entry[:8].decode('ascii').rstrip()
        extension=bytes(c&0x7f for c in entry[8:]).decode('ascii').rstrip()
        value=prefix+basename+('.'+extension if extension else '')
        length=len(value)+1
        initial=S('for_items')+(4096-length if exact else 4095 if overflow else 0)
        expected_end=initial if overflow else initial+length
        entry_bytes=b'\0'+entry+bytes(20)
        body=f'''bits 16
cpu 8086
org 100h
 cld
 mov ax,cs
 add ax,(production-$$+100h)/16
 mov [target+2],ax
 mov ax,cs
 add ax,(state-$$+100h)/16
 mov ds,ax
 mov es,ax
 mov word [{S('for_end')}],{initial}
 mov byte [{S('condition_error')}],0
 mov byte [{S('for_items')+4096}],55h
 mov byte [{S('for_value')+144}],55h
 mov si,prefix
 mov di,{S('for_prefix')}
copy_prefix:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_prefix
 mov si,entry
 mov di,0f100h
 mov cx,32
copy_entry:
 mov al,[cs:si]
 inc si
 stosb
 loop copy_entry
 mov bx,0f100h
 call far [cs:target]
 pushf
 pop ax
 and ax,1
 cmp ax,{int(overflow)}
 jne failed
 cmp word [{S('for_end')}],{expected_end}
 jne failed
 cmp byte [{S('for_items')+4096}],55h
 jne failed
 cmp byte [{S('for_value')+144}],55h
 jne failed
 cmp byte [{S('condition_error')}],{3 if overflow else 0}
 jne failed
'''
        if not overflow:
            body+=f''' mov si,expected
 mov di,{initial}
compare_value:
 mov al,[cs:si]
 inc si
 cmp al,[di]
 jne failed
 inc di
 or al,al
 jnz compare_value
 mov bx,0f100h
 call far [cs:target]
 jc failed
 cmp word [{S('for_end')}],{expected_end}
 jne failed
'''
        body+=f''' mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
target dw {entries['for_collect_file']},0
prefix db {db(prefix)}
entry db {','.join(str(c) for c in entry_bytes)}
expected db {db(value)}
align 16
production: incbin "code.bin"
align 16
state: incbin "data.bin"
'''
        (folder/'test.asm').write_text(body)
        subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=folder,check=True,capture_output=True)
        result=subprocess.run(['emu2','test.com'],cwd=folder,capture_output=True,timeout=5)
        assert result.returncode==0,(prefix,entry,exact,overflow,result.stderr)
print('PASS: snapshot callback deduplication, CP/M attribute bits, long path values, exact fit and overflow canaries')
print(f'PASS: {len(cases)} production-byte FOR cases: quoted lists, ranges/endpoints/overflow, one-pass expansion, variable rendering, empty provenance and syntax recovery')
