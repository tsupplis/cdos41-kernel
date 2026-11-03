#!/usr/bin/env python3
"""Execute the linked FAT raw search and ordinary-entry filter.

Only sector reading, record-size conversion and output formatting are stubbed.
Label discovery/filtering, restart, metadata synthesis and stack handling are
production instructions. NASM builds a disposable test driver, not the kernel.
"""

from historical_check import symbols, payload, word
from pctmp_recovery_check import asm
from fat_recovery_check import separate_near, hook

D = symbols("pcbdos")
B = symbols("black")
base = symbols("bdos")["PCSEARCH"] - B["PCSEARCH"]
C = lambda n: base + B[n]


def entry(name, attr, first=None):
    b = bytearray(32)
    b[:11] = name.encode().ljust(11, b" ")
    b[11] = attr
    if first is not None:
        b[0] = first
    return bytes(b)


file1 = entry("FIRST   TXT", 0x20)
file2 = entry("SECOND  TXT", 0x20)
label = entry("DOSVOL", 8)
empty = bytes(32)
lfn = entry("LONGNAME", 15)
deleted = entry("DEADLABEL", 8, 0xE5)
# Expected records: first byte, name (or None when irrelevant).
cases = [
    ([label, file1, empty], [(32, "DOSVOL"), (0, "FIRST   TXT"), (229, None)]),
    ([file1, label, empty], [(32, "DOSVOL"), (0, "FIRST   TXT"), (229, None)]),
    ([file1, empty], [(32, ""), (0, "FIRST   TXT"), (229, None)]),
    ([empty], [(32, ""), (229, None)]),
    ([deleted, file1, empty], [(32, ""), (229, None), (0, "FIRST   TXT"), (229, None)]),
    ([lfn, file1, label], [(32, "DOSVOL"), (0, "FIRST   TXT")]),
    ([lfn, empty], [(32, ""), (229, None)]),
    ([label, empty], [(32, "DOSVOL"), (229, None)]),
    ([file1, file2, label], [(32, "DOSVOL"), (0, "FIRST   TXT"), (0, "SECOND  TXT")]),
    ([entry("BADDIR", 0x18), label, file1], [(32, "DOSVOL"), (0, "FIRST   TXT")]),
    ([entry("OLDVOL", 8), label, file1], [(32, "OLDVOL"), (0, "FIRST   TXT")]),
    ([entry("DOSVOL", 32), label], [(32, "DOSVOL"), (0, "DOSVOL")]),
]
count = 0
for mode in [0, 2]:
    for records, raw_expected in cases:
        code = bytearray(payload("bdos"))
        hook(
            code,
            D["RD_PCDIR"],
            f"""inc word [{D['DCNT']}]
 mov bx,[{D['DCNT']}]
 cmp bx,{len(records)}
 jae no_entry
 mov cl,5
 shl bx,cl
 lea ax,[bx+0f200h]
 ret
no_entry:
 xor ax,ax
 ret
""",
        )
        hook(code, D["LRET_EQ_FF"], f'mov byte [{D["LRET"]}],255\nret')
        hook(code, C("EXTSIZE"), "mov ax,65535\nret")
        hook(code, C("SETSFCB"), "ret")
        hook(code, C("MATCH"), "mov al,1\nret")
        hook(
            code,
            C("COPYDIR"),
            f"""push bp
 mov bp,sp
 mov di,[ss:bp+4]
 mov bx,[{D['DIRP']}]
 test byte [bx+11],8
 jz good_file
 mov byte [0f010h],1
good_file:
 xor al,al
 stosb
 mov si,bx
 mov cx,11
 rep movsb
 pop bp
 ret
""",
        )
        worker = len(code)
        code += asm(f"""org {worker}
 mov cl,{mode}
 cmp byte [0f000h],0
 jne next_search
 inc byte [0f000h]
 xor ax,ax
 jmp enter_search
next_search:
 mov ax,1
 or ax,ax
enter_search:
 pushf
 jmp {C('PCSEARCH')}
""")
        expected = (
            raw_expected
            if mode == 0
            else [
                (0, r[:11].decode().rstrip())
                for r in records
                if r[0] not in [0, 229] and not (r[11] & 8)
            ]
        )
        body = f"""mov word [{D['DMA_SEG']}],ds
 mov word [{D['DMA_OFST']}],0f600h
 mov byte [{D['HDIRFX']}],0
 mov byte [{D['INFO_FCB']+12}],63
 mov word [{D['HDSADDR']}],0f100h
 mov byte [0f000h],0
 mov byte [0f010h],0
 mov byte [0f680h],055h
"""
        for i, r in enumerate(records):
            body += "".join(
                f"mov byte [{0xf200+32*i+j}],{v}\n" for j, v in enumerate(r)
            )
        for first, name in expected:
            body += f"""mov [0f020h],sp
 mov byte [{D["LRET"]}],0
 call far [cs:target]
 cmp sp,[0f020h]
 jne failed
 cmp byte [{D["LRET"]}],0
 jne failed
 cmp byte [0f600h],{first}
 jne failed
 cmp byte [0f010h],0
 jne failed
 cmp byte [0f680h],055h
 jne failed
"""
            if name is not None:
                for i, v in enumerate(name.encode().ljust(11, b" ")):
                    body += f"cmp byte [{0xf601+i}],{v}\njne failed\n"
            if first == 32:
                for offset, value in [
                    (12, 0x21),
                    (15, 128),
                    (16, 128),
                    (17, 128),
                    (96, 0x21),
                ]:
                    body += f"cmp byte [{0xf600+offset}],{value}\njne failed\n"
        body += f'call far [cs:target]\ncmp byte [{D["LRET"]}],255\njne failed\n'
        try:
            separate_near(code, worker, body)
        except AssertionError as exc:
            raise AssertionError((mode, records, expected, exc)) from exc
        count += 1
print(
    f"PASS: {count} linked FAT searches: first/later/missing/deleted labels, LFN metadata, full/empty directories, duplicate labels, same-name file, ordinary/raw filtering, DMA bounds and stack balance"
)
