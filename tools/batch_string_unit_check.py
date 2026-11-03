#!/usr/bin/env python3
"""Execute linked BATCH IF string parsing/comparison in a disposable DOS driver.

Production bytes perform parsing, quote handling, comparison, NOT and nested
redispatch. Diagnostics are counted; filesystem probes are forbidden here.
The NASM driver is test-only and never ships as a command.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
symbols = {}
pending = None
for line in (ROOT / "commands/batch/batch.lst").read_text(errors="replace").splitlines():
    label = re.match(r"^=\s+([A-Za-z_][A-Za-z_0-9]*):",line)
    if label:
        pending=label[1].upper()
    address=re.match(r"^=([0-9A-F]{4})\s+",line)
    if address:
        if pending:
            symbols[pending]=int(address[1],16);pending=None
        decl=re.search(r"\b([A-Za-z_][A-Za-z_0-9]*)\s+(?:db|dw|dd|rb|rs|rw|rd)\b",line,re.I)
        if decl:
            symbols[decl[1].upper()]=int(address[1],16)+0x100
S=lambda name:symbols[name.upper()]
command=(ROOT/"commands/batch/batch.cmd").read_bytes()
length=int.from_bytes(command[1:3],"little")*16
code=bytearray(command[128:128+length])
data=bytes(256)+command[128+length:128+length+int.from_bytes(command[10:12],"little")*16]
# Only diagnostics and the deliberately forbidden I/O boundary are replaced.
code[S("print_string"):S("print_string")+5]=b"\xfe\x06\x01\xf0\xc3"
code[S("crlf")]=0xc3
code[S("condition_probe"):S("condition_probe")+6]=b"\xc6\x06\x00\xf0\x01\xc3"
entry=len(code)
code+=b"\xe8"+((S("batch_condition")-entry-3)&65535).to_bytes(2,"little")+b"\xcb"
expansion_entry=len(code)
code+=b"\xe8"+((S("batch_expand")-expansion_entry-3)&65535).to_bytes(2,"little")+b"\xcb"

# A result string is the exact remaining command; None means false, ERROR
# means a syntax diagnostic. Quoting follows DOS literal-byte comparison.
cases=[
 ("IF abc==abc ECHO Mixed $ Text","ECHO Mixed $ Text"),
 ("IF abc==ABC ECHO WRONG",None),
 ("if not abc==ABC ECHO CaseSensitive","ECHO CaseSensitive"),
 ('IF "abc"=="abc" ECHO yes','ECHO yes'),
 ('IF "abc"==abc ECHO WRONG',None),
 ('IF NOT "abc"==abc ECHO yes','ECHO yes'),
 ('IF ""=="" ECHO empty','ECHO empty'),
 ('IF NOT ""=="" ECHO WRONG',None),
 ('IF " "=="" ECHO WRONG',None),
 ('IF " a b " == " a b " ECHO spaces','ECHO spaces'),
 ('IF "a\tb"=="a\tb" ECHO tabs','ECHO tabs'),
 ('IF "a==b"=="a==b" ECHO operator','ECHO operator'),
 ('IF a=b==a=b ECHO single','ECHO single'),
 ('IF 01==1 ECHO WRONG',None),
 ('IF "a*?"=="a*?" ECHO literal','ECHO literal'),
 ('IF EXIST==EXIST ECHO keyword','ECHO keyword'),
 ('IF DIREXIST==DIREXIST ECHO keyword','ECHO keyword'),
 ('IF NOT==NOT ECHO keyword','ECHO keyword'),
 ('IF NOT NOT==NOT ECHO WRONG',None),
 ('IF A==A IF B==B ECHO nested','ECHO nested'),
 ('IF A==A IF B==b ECHO WRONG',None),
 ('IF A==b IF unsupported ECHO WRONG',None),
 ('IF "a""b"=="a""b" ECHO quotes','ECHO quotes'),
 ('IF \x82==\x82 ECHO bytes','ECHO bytes'),
 ('IF "'+"x"*55+'"=="'+"x"*55+'" ECHO X','ECHO X'),
 ('ECHO not-an-if','ECHO not-an-if'),
 ('IFFY foo','IFFY foo'),
]
for left in ["", " ", "\t", " \t"]:
    for right in ["", " ", "\t", "\t "]:
        cases.append((f'IF "x y"{left}=={right}"x y" ECHO spacing','ECHO spacing'))
for text in ['IF','IF NOT','IF ==a ECHO WRONG','IF a=b ECHO WRONG','IF a!=b ECHO WRONG',
             'IF a==a','IF a == a   ','IF "a==a ECHO WRONG','IF a=="a ECHO WRONG',
             'IF a b==a ECHO WRONG','IF /I a==A ECHO WRONG','IF= a==a ECHO WRONG']:
    cases.append((text,"ERROR"))


# These cases execute expansion first, preserving empty-token provenance.
# In particular, a multiword command must not supply a missing RHS operand.
for text,expected,environment in [
 ('IF %MISSING% == VALUE ECHO wrong left','ERROR',b'\0\0'),
 ('IF VALUE == %MISSING% ECHO wrong right','ERROR',b'\0\0'),
 ('IF %MISSING%==VALUE ECHO wrong left','ERROR',b'\0\0'),
 ('IF VALUE==%MISSING% ECHO wrong right','ERROR',b'\0\0'),
 ('IF NOT VALUE==%MISSING% ECHO wrong not','ERROR',b'\0\0'),
 ('IF VALUE==%NAME% ECHO wrong empty','ERROR',b'NAME=\0\0'),
 ('IF x==x IF VALUE==%MISSING% ECHO wrong nested','ERROR',b'\0\0'),
 ('IF x==x IF y==y IF VALUE==%MISSING% ECHO wrong nested','ERROR',b'\0\0'),
 ('IF x==X IF VALUE==%MISSING% ECHO unreachable',None,b'\0\0'),
 ('IF "%MISSING%"=="" ECHO quoted','ECHO quoted',b'\0\0'),
 ('IF "%MISSING%TOTO"=="TOTO" ECHO suffix','ECHO suffix',b'\0\0'),
 ('IF %MISSING%TOTO==TOTO ECHO suffix','ECHO suffix',b'\0\0'),
 ('IF x==x%MISSING% ECHO trailing','ECHO trailing',b'\0\0'),
 ('IF x==%MISSING%%OTHER% ECHO adjacent','ECHO adjacent',b'OTHER=x\0\0'),
 ('IF x==x ECHO %MISSING% tail','ECHO  tail',b'\0\0'),
 ('IF VALUE==%9 ECHO missing positional','ERROR',b'\0\0'),
 ('IF %9==VALUE ECHO missing positional','ERROR',b'\0\0'),
 ('IF "%9"=="" ECHO quoted positional','ECHO quoted positional',b'\0\0'),
]:
    cases.append((text,expected,environment))

def db(value):
    return ",".join(str(c) for c in value.encode("latin1")+b"\0")
with tempfile.TemporaryDirectory(prefix="cdos-if-string-unit-") as folder_name:
    folder=Path(folder_name)
    (folder/"code.bin").write_bytes(code);(folder/"data.bin").write_bytes(data)
    for number,case in enumerate(cases):
        text,expected=case[:2]
        environment=case[2] if len(case)>2 else None
        environment_bytes=environment if environment is not None else b"\0\0"
        assert len(text)<=127,(number,len(text))
        skip=expected is None or expected=="ERROR"
        source=f'''bits 16
cpu 8086
org 100h
 cld
 mov ax,cs
 add ax,(production-$$+100h)/16
 mov [target+2],ax
 mov [expansion_target+2],ax
 mov ax,cs
 add ax,(state-$$+100h)/16
 mov ds,ax
 mov es,ax
 mov word [0f000h],0
 mov di,{S("expand_empty_positions")}
 mov cx,128
 xor al,al
 rep stosb
 mov word [{S("subparms")}],0
 mov word [{S("ms_func_jmp_addr")}],query
 mov ax,cs
 mov word [{S("ms_func_jmp_addr")+2}],ax
 mov byte [{S('read_blen')}],{len(text)+1}
 mov si,input_line
 mov di,{S('clicb_cmd')}
copy_input:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_input
 {"call far [cs:expansion_target]" if environment is not None else "clc"}
 jc failed
 call far [cs:target]
 pushf
 pop ax
 and ax,1
 cmp ax,{int(skip)}
 jne failed
 cmp byte [0f000h],0
 jne failed
 cmp byte [0f001h],{int(expected=='ERROR')}
 jne failed
'''
        if not skip:
            source+=f''' mov si,expected_line
 mov di,{S('clicb_cmd')}
compare:
 mov al,[cs:si]
 inc si
 cmp al,[di]
 jne failed
 inc di
 or al,al
 jnz compare
 cmp byte [{S('read_blen')}],{len(expected)+1}
 jne failed
'''
        source+=f''' mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
query:
 mov ax,cs
 add ax,(environment-$$+100h)/16
 mov dx,{len(environment_bytes)}
 retf
target dw {entry},0
expansion_target dw {expansion_entry},0
input_line db {db(text)}
expected_line db {db(expected or '')}
align 16
production: incbin "code.bin"
align 16
state: incbin "data.bin"
align 16
environment db {",".join(str(c) for c in environment_bytes)}
'''
        (folder/"test.asm").write_text(source)
        subprocess.run(["nasm","-f","bin","test.asm","-o","test.com"],cwd=folder,check=True,capture_output=True)
        result=subprocess.run(["emu2","test.com"],cwd=folder,capture_output=True,timeout=5)
        assert result.returncode==0,(number,text,expected,result.stdout,result.stderr)
print(f"PASS: {len(cases)} linked IF comparison cases: case/quotes/empty operands, spacing, operator text, literal keywords, NOT, nested dispatch, malformed syntax, unquoted empty substitutions, nested provenance and no filesystem calls")
