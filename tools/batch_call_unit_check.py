#!/usr/bin/env python3
"""Execute production CALL wrapper bytes with synthetic native parser/search.

Native BDOS 152 itself is exercised by batch_call_check.py. Here its returned
FCB/status is controlled to isolate validation, atomic bounds and caller state.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
symbols={};pending=None
for line in (ROOT/'commands/batch/batch.lst').read_text(errors='replace').splitlines():
    label=re.match(r'^=\s+([A-Za-z_][A-Za-z_0-9]*):',line)
    if label: pending=label[1].upper()
    address=re.match(r'^=([0-9A-F]{4})\s+',line)
    if address:
        if pending: symbols[pending]=int(address[1],16);pending=None
        decl=re.search(r'\b([A-Za-z_][A-Za-z_0-9]*)\s+(?:db|dw|dd|rb|rs|rw|rd)\b',line,re.I)
        if decl: symbols[decl[1].upper()]=int(address[1],16)+0x100
S=lambda n:symbols[n.upper()]
cmd=(ROOT/'commands/batch/batch.cmd').read_bytes();size=int.from_bytes(cmd[1:3],'little')*16
original=bytearray(cmd[128:128+size])
data=bytes(256)+cmd[128+size:128+size+int.from_bytes(cmd[10:12],'little')*16]
# Native 152 returns the fixture FCB, preloaded below. No filesystem is used.
original[S('print_string'):S('print_string')+5]=b'\xfe\x06\x01\xf0\xc3'
original[S('crlf')]=0xc3
cases=[
 ('CALL B:CHILD.BAT MiXeD $ Text','BATCH.CMD B:CHILD.BAT MiXeD $ Text','BAT',True,'B:CHILD.BAT'),
 ('call child ArgCase','BATCH.CMD child ArgCase','   ',True,'child.BAT'),
 ('CALL b:child.bat %%NAME%','BATCH.CMD b:child.bat %%NAME%','BAT',True,'b:child.bat'),
 ('CALL B:CHILD.BAT "AA AA"','BATCH.CMD B:CHILD.BAT "AA AA"','BAT',True,'B:CHILD.BAT'),
 ('CALL B:CHILD.BAT '+'x'*105,'BATCH.CMD B:CHILD.BAT '+'x'*105,'BAT',True,'B:CHILD.BAT'),
 ('CALL B:CHILD.BAT '+'x'*106,None,'BAT',True,None),
 ('CALL B:CHILD.BAT',None,'BAT',False,None),
 ('CALL B:CHILD.TXT',None,'TXT',True,None),
 ('CALL B:CHILD.CMD',None,'CMD',True,None),
 ('CALL',None,'BAT',True,None),
 ('CALL  B:CHILD.BAT',None,'BAT',True,None),
 ('CALL   ',None,'BAT',True,None),
 ('CALL=child',None,'BAT',True,None),
 ('CALL "B:CHILD.BAT"',None,'BAT',True,None),
 ('CALL B:\\SUB\\CHILD.BAT',None,'BAT',True,None),
 ('CALL B:/CHILD.BAT',None,'BAT',True,None),
 ('CALL B:CHILD.BAT;password',None,'BAT',True,None),
 ('CALL B:*.BAT',None,'BAT',True,None),
 ('CALL :label',None,'BAT',True,None),
 ('CALL badfilenamehere',None,'BAT',True,None),
 ('CALLER stays literal','CALLER stays literal','BAT',True,None),
 ('CALL.CMD stays literal','CALL.CMD stays literal','BAT',True,None),
]
def db(s):return ','.join(str(c) for c in s.encode('latin1')+b'\0')
with tempfile.TemporaryDirectory(prefix='cdos-call-unit-') as name:
    folder=Path(name);(folder/'data.bin').write_bytes(data)
    for number,(source,result,extension,found,lookup) in enumerate(cases):
        code=bytearray(original)
        code[S('condition_probe'):S('condition_probe')+11]=b'\xc6\x06'+S('condition_result').to_bytes(2,'little')+bytes([int(found)])+b'\xc6\x06'+S('condition_error').to_bytes(2,'little')+b'\0\xc3'
        parse_bad=source in ['CALL :label','CALL badfilenamehere']
        stub=len(code)
        code+=b'\x31\xdb\x49\x90\xc3' if parse_bad else b'\x31\xdb\x31\xc9\xc3'
        # CCPM is only three bytes; jump to the stub without overwriting
        # the following lang_word routine.
        code[S('ccpm'):S('ccpm')+3]=b'\xe9'+((stub-S('ccpm')-3)&65535).to_bytes(2,'little')
        entry=len(code);code+=b'\xe8'+((S('batch_call')-entry-3)&65535).to_bytes(2,'little')+b'\xcb'
        capture_entry=len(code)
        code+=b'\xe8'+((S('batch_capture_status')-capture_entry-3)&65535).to_bytes(2,'little')+b'\xcb'
        (folder/'code.bin').write_bytes(code)
        fcb=bytes([2])+('CHILD   '+extension).encode()+bytes(24)
        if '*' in source:fcb=bytes([2])+b'????????BAT'+bytes(24)
        handled=not source.startswith(('CALLER','CALL.CMD'))
        error=result is None
        empty_marker=S('expand_empty_positions')+5
        body=f'''bits 16
cpu 8086
org 100h
 cld
 mov ax,cs
 add ax,(production-$$+100h)/16
 mov [target+2],ax
 mov [capture_target+2],ax
 mov ax,cs
 add ax,(state-$$+100h)/16
 mov ds,ax
 mov es,ax
 mov byte [0f001h],0
 mov byte [{empty_marker}],{int(source=='CALL  B:CHILD.BAT')}
 mov byte [{S('for_kind')}],1
 mov word [{S('for_cursor')}],1234h
 mov word [{S('batch_errorlevel')}],7
 mov byte [{S('batch_echo')}],55h
 mov byte [{S('call_pending')}],0
 mov byte [{S('read_blen')}],{len(source)+1}
 mov si,input_line
 mov di,{S('clicb_cmd')}
copy_input:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_input
 mov si,fixture
 mov di,{S('call_fcb')}
 mov cx,36
copy_fcb:
 mov al,[cs:si]
 inc si
 stosb
 loop copy_fcb
 call far [cs:target]
 pushf
 pop ax
 and ax,1
 cmp ax,{int(error)}
 jne failed
 cmp byte [0f001h],{int(error)}
 jne failed
 cmp word [{S('batch_errorlevel')}],{1 if error else 7}
 jne failed
 cmp byte [{S('call_pending')}],{int(handled and not error)}
 jne failed
 cmp byte [{S('for_kind')}],1
 jne failed
 cmp word [{S('for_cursor')}],1234h
 jne failed
 cmp byte [{S('batch_echo')}],55h
 jne failed
 mov si,expected
 mov di,{S('clicb_cmd')}
compare:
 mov al,[cs:si]
 inc si
 cmp al,[di]
 jne failed
 inc di
 or al,al
 jnz compare
 cmp byte [{S('read_blen')}],{len(result if result is not None else source)+1}
 jne failed
'''
        if lookup is not None:
            body+=f''' mov si,lookup
 mov di,{S('condition_spec')}
compare_lookup:
 mov al,[cs:si]
 inc si
 cmp al,[di]
 jne failed
 inc di
 or al,al
 jnz compare_lookup
'''
        if handled and not error:
            body+=f''' mov byte [{S('batch_status_pending')}],0
 call far [cs:capture_target]
 cmp word [{S('batch_errorlevel')}],1
 jne failed
 cmp byte [{S('call_pending')}],0
 jne failed
'''
        body+=f''' mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
target dw {entry},0
capture_target dw {capture_entry},0
input_line db {db(source)}
expected db {db(result if result is not None else source)}
lookup db {db(lookup or '')}
fixture db {','.join(str(c) for c in fcb)}
align 16
production: incbin "code.bin"
align 16
state: incbin "data.bin"
'''
        (folder/'test.asm').write_text(body)
        subprocess.run(['nasm','-f','bin','test.asm','-o','test.com'],cwd=folder,capture_output=True,check=True)
        try:
            result_code=subprocess.run(['emu2','test.com'],cwd=folder,capture_output=True,timeout=5)
        except subprocess.TimeoutExpired as error:
            raise AssertionError((number,source,'test driver timeout')) from error
        assert result_code.returncode==0,(number,source,result,result_code.stderr)
print(f'PASS: {len(cases)} production-byte CALL cases: BAT extension/default, case/tail preservation, exact 127-byte wrapper, overflow atomicity, validation/failure and FOR/echo/status preservation')
