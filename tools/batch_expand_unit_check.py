#!/usr/bin/env python3
"""Execute assembled BATCH expansion with synthetic environment-query results.

Only environment discovery and diagnostic output are stubbed. All parsing,
lookup, bounds, copying and argument expansion execute the production bytes.
The disposable NASM DOS driver is never part of a shipped command.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
listing = (ROOT / "commands/batch/batch.lst").read_text(errors="replace")
symbols = {}
pending = None
for line in listing.splitlines():
    label = re.match(r"^=\s+([A-Za-z_][A-Za-z_0-9]*):", line)
    if label:
        pending = label[1].upper()
    address = re.match(r"^=([0-9A-F]{4})\s+", line)
    if address:
        if pending:
            symbols[pending] = int(address[1], 16)
            pending = None
        decl = re.search(r"\b([A-Za-z_][A-Za-z_0-9]*)\s+(?:db|dw|dd|rb|rs|rw|rd)\b", line, re.I)
        if decl:
            symbols[decl[1].upper()] = int(address[1], 16)
# LINKCMD gives the native DATA group a 100h load origin. RASM's listing
# contains its pre-link offsets; the CMD stores the load image without the
# native basepage. Match the real loader rather than aliasing DATA and CODE.
for name in ["batch_echo", "goto_target", "expand_available", "expand_line",
             "expand_environment", "ms_func_jmp_addr", "long_line",
             "clicb_cmd", "subparms", "read_blen"]:
    symbols[name.upper()] += 0x100
S = lambda name: symbols[name.upper()]
# No BATCH state is allowed in the native basepage or before the TMP data.
assert S("batch_echo") >= S("subparms") + 128
assert S("goto_target") + 128 <= S("expand_available")
assert S("expand_line") + 128 <= S("expand_environment")
command = (ROOT / "commands/batch/batch.cmd").read_bytes()
code_len = int.from_bytes(command[1:3], "little") * 16
data_len = int.from_bytes(command[10:12], "little") * 16
code = bytearray(command[128:128+code_len])
data = bytes(256) + command[128+code_len:128+code_len+data_len]
for name in ["print_string", "crlf"]:
    code[S(name)] = 0xc3
entry = len(code)
code += b"\xe8" + ((S("batch_expand")-entry-3) & 65535).to_bytes(2,"little") + b"\xcb"

cases = [
    ("ECHO %NaMe%", b"NAME=MiXeD$\0\0", "ECHO MiXeD$"),
    ("%MISSING%:%NAME%", b"NAME=value\0\0", ":value"),
    ("%%NAME%%", b"NAME=wrong\0\0", "%NAME%"),
    ("%1", b"NAME=wrong\0\0", "%NAME%"),
    ("%NAME%", b"NAME=%1%%\0\0", "%1%%"),
    ("unmatched%NAME", b"\0\0", "unmatched%NAME"),
    ("%0:%9:%10", b"\0\0", "demo::%NAME%0"),
    ('"%NAME%"', b"NAME=with spaces\0\0", '"with spaces"'),
    ("X"*127, b"\0\0", "X"*127),
    ("%WIDE%", b"WIDE="+b"X"*127+b"\0\0", "X"*127),
    ("%WIDE%X", b"WIDE="+b"X"*127+b"\0\0", None),
    ("%NAME%", b"\0\0", ""),
    ("%NAME%", b"NAMEX=no\0NAME=yes\0\0", "yes"),
    ("%NAME%", b"MALFORMED\0NAME=yes\0\0", "yes"),
]
# Unknown API, bad capacities and missing terminators fail safely only when
# a named variable is requested. Positional/escaped forms need no environment.
for capacity in [0,1,1025,65535]:
    cases += [("%NAME%", b"NAME=x\0\0", None, capacity),
              ("%1 %%", b"NAME=x\0\0", "%NAME% %", capacity)]
cases += [("%NAME%", b"X"*1024, None),
          ("%NAME%", b"NAME=x\0X", None),
          ("ECHO NO", b"\0\0", None, 2, True)]

def db(value):
    return ",".join(str(c) for c in value)

with tempfile.TemporaryDirectory(prefix="cdos-expand-unit-") as temp:
    folder = Path(temp)
    (folder/"code.bin").write_bytes(code)
    (folder/"data.bin").write_bytes(data)
    for number, case in enumerate(cases):
        text, environment, expected, *options = case
        capacity = options[0] if options else len(environment)
        too_long = bool(options[1]) if len(options)>1 else False
        expected_carry = 1 if expected is None else 0
        # The malformed API fixture's advertised length is tested before reads.
        source = f'''bits 16
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
 mov byte [{S('long_line')}],{255 if too_long else 0}
 mov si,input_line
 mov di,{S('clicb_cmd')}
copy_input:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_input
 mov si,arguments
 mov di,{S('subparms')}
copy_args:
 mov al,[cs:si]
 inc si
 stosb
 or al,al
 jnz copy_args
 call far [cs:target]
 pushf
 pop ax
 and ax,1
 cmp ax,{expected_carry}
 jne failed
'''
        if expected is not None:
            source += f''' mov si,expected_line
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
        else:
            # Failure must not commit even a partially expanded command.
            source += f''' mov si,input_line
 mov di,{S('clicb_cmd')}
compare_original:
 mov al,[cs:si]
 inc si
 cmp al,[di]
 jne failed
 inc di
 or al,al
 jnz compare_original
'''
        source += f''' mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
query:
 mov ax,0ffffh
 mov dx,{capacity}
 cmp dx,65535
 je query_done
 mov ax,cs
 add ax,(environment-$$+100h)/16
query_done:
 retf
target: dw {entry},0
input_line: db {db(text.encode()+bytes([0]))}
arguments: db {db(b'demo %NAME% second '+bytes([0]))}
expected_line: db {db((expected or '').encode()+bytes([0]))}
align 16
production: incbin "code.bin"
align 16
state: incbin "data.bin"
align 16
environment: db {db(environment)}
'''
        (folder/"test.asm").write_text(source)
        subprocess.run(["nasm","-f","bin","test.asm","-o","test.com"],cwd=folder,check=True,capture_output=True)
        result = subprocess.run(["emu2","test.com"],cwd=folder,capture_output=True,timeout=5)
        if result.returncode:
            import shutil
            saved = Path(tempfile.mkdtemp(prefix="cdos-expand-unit-failed-"))
            for name in ["test.asm", "test.com", "code.bin", "data.bin"]:
                shutil.copyfile(folder/name, saved/name)
            raise AssertionError((number, case, saved, result.stdout, result.stderr))
print(f"PASS: {len(cases)} production-byte expansion cases, unavailable/malformed environment, bounds, nonrecursive values and BATCH state layout")
