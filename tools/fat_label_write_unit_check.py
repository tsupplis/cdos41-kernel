#!/usr/bin/env python3
"""Execute BDOS 100's FAT writer; stub only sector/cache/error dependencies."""

from historical_check import symbols, payload
from pctmp_recovery_check import asm
from fat_recovery_check import hook, separate_near

D = symbols("pcbdos")
B = symbols("black")
base = symbols("bdos")["PCSEARCH"] - B["PCSEARCH"]
C = lambda n: base + B[n]


def record(name, attribute):
    b = bytearray(32)
    b[:11] = name.encode().ljust(11, b" ")
    b[11] = attribute
    return bytes(b)


ordinary = record("KEEP    TXT", 32)
volume = record("OLDLABEL", 8)
empty = bytes(32)
cases = [
    ([ordinary, empty], "newlabel", 0, False, 0, 1, 1),
    ([ordinary, volume, empty], "MY DISK", 0, False, 0, 1, 1),
    ([ordinary, volume], "RENAMED", 0, False, 0, 1, 1),
    ([ordinary, volume, empty], "", 0, False, 0, 1, 1),
    ([ordinary, empty], "", 0, False, 0, 0, None),
    ([ordinary], "FULL", 0, False, 255, 0, None),
    ([ordinary, volume], "ROTEST", 0, True, 255, 0, None),
]
for flags in [1, 0x10, 0x20, 0x40, 0x80, 0xFF]:
    cases.append(([ordinary, volume], "BADFLAGS", flags, False, 255, 0, None))
for name in [
    " BAD",
    "BAD?",
    "BAD*",
    "BAD.NAME",
    "BAD/NAME",
    "BAD:NAME",
    "BAD=NAME",
    "BAD\\NAME",
    "\x00BAD",
    "\x7fBAD",
]:
    cases.append(([ordinary, volume], name, 0, False, 255, 0, None))

for records, name, flags, readonly, status, writes, changed in cases:
    code = bytearray(payload("bdos"))
    hook(
        code,
        D["RD_PCDIR"],
        f"""cmp word [{D['HDSADDR']}],0
 je root_ok
 mov byte [0f014h],1
root_ok:
 inc word [{D['DCNT']}]
 mov bx,[{D['DCNT']}]
 cmp bx,{len(records)}
 jae done
 mov cl,5
 shl bx,cl
 lea ax,[bx+0f200h]
 ret
done:
 xor ax,ax
 ret
""",
    )
    hook(
        code,
        D["CHECKWRITE"],
        (
            f"""mov byte [{D['LRET']}],255
 pop ax
 ret
"""
            if readonly
            else "ret"
        ),
    )
    hook(code, D["LRET_EQ_FF"], f'mov byte [{D["LRET"]}],255\nret')
    hook(code, D["WRDIR"], "inc byte [0f010h]\nret")
    hook(code, D["FLUSH"], "inc byte [0f011h]\nret")
    hook(code, D["SETCDR"], "ret")
    hook(code, C("CNVCPD"), "ret")
    hook(code, C("SETPCD"), "ret")
    body = f"""mov word [{D['HDSADDR']}],0f100h
 mov byte [{D['INFO_FCB']+12}],{flags}
 mov byte [{D['LRET']}],0
 mov word [0f010h],0
 mov byte [0f014h],0
"""
    for i, value in enumerate(name.encode().ljust(11, b" ")):
        body += f'mov byte [{D["INFO_FCB"]+1+i}],{value}\n'
    for i, r in enumerate(records):
        body += "".join(f"mov byte [{0xf200+32*i+j}],{v}\n" for j, v in enumerate(r))
    body += f"""mov [0f020h],sp
 call far [cs:target]
 cmp sp,[0f020h]
 jne failed
 cmp byte [{D['LRET']}],{status}
 jne failed
 cmp word [{D['HDSADDR']}],0f100h
 jne failed
 cmp byte [0f014h],0
 jne failed
 cmp byte [0f010h],{writes}
 jne failed
 cmp byte [0f011h],{writes}
 jne failed
"""
    for i, old in enumerate(records):
        wanted = bytearray(old)
        if i == changed:
            if not name:
                wanted[0] = 229
            else:
                wanted[:] = bytes(32)
                wanted[:11] = name.upper().encode().ljust(11, b" ")
                wanted[11] = 8
        body += "".join(
            f"cmp byte [{0xf200+32*i+j}],{v}\njne failed\n"
            for j, v in enumerate(wanted)
        )
    try:
        separate_near(code, C("PC_SET_LABEL"), body)
    except AssertionError as exc:
        raise AssertionError((name, flags, readonly, exc)) from exc
print(
    f"PASS: {len(cases)} BDOS FAT label writes: create/rename/delete, spaces, full/RO disks, invalid names/CPM metadata, same-directory file preservation and root/mapping restoration"
)
