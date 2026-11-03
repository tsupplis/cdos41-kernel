#!/usr/bin/env python3
"""Execute real FAT DELETEF/GETDIR: HIDDEN/SYSTEM versus READ-ONLY.

Sector/cache/allocation and lock dependencies are stubbed; selection,
two-pass deletion and attribute checks are the assembled production code.
"""

from historical_check import symbols, payload
from fat_recovery_check import hook, separate_near

D = symbols("pcbdos")
B = symbols("black")
base = symbols("bdos")["PCSEARCH"] - B["PCSEARCH"]
C = lambda name: base + B[name]
count = 0
for wildcard in [False, True]:
    for flags in [0, 2, 4, 6, 1, 3, 5, 7]:
        code = bytearray(payload("bdos"))
        hook(
            code,
            D["RD_PCDIR"],
            f"""inc word [{D['DCNT']}]
 cmp word [{D['DCNT']}],1
 jae enddir
 mov ax,0f200h
 ret
enddir:
 xor ax,ax
 ret
""",
        )
        for name in ["TST_OLIST", "CHK_OLIST", "UPDATE_FAT"]:
            hook(code, D[name], "ret")
        hook(code, C("DELFAT"), "inc byte [0f010h]\nret")
        hook(code, D["WRDIR"], "inc byte [0f011h]\nret")
        # Native error path resets the BDOS stack. Discard its saved AX.
        hook(code, D["ROFERROR"], f"mov word [{D['ARET']}],03ffh\npop ax\nret")
        body = f"""mov word [{D['ARET']}],0
 mov word [{D['HDSADDR']}],0f100h
 mov word [0f010h],0
 mov byte [{D['INFO_FCB']}],2
 mov byte [0f200h],'F'
 mov byte [0f20bh],{0x20|flags}
 mov word [0f21ah],7
"""
        for i, v in enumerate(b"FILE    TXT"):
            body += f"mov byte [{0xf200+i}],{v}\n"
        for i, v in enumerate(b"???????????" if wildcard else b"FILE    TXT"):
            body += f'mov byte [{D["INFO_FCB"]+1+i}],{v}\n'
        body += f"""mov [0f020h],sp
 call far [cs:target]
 cmp sp,[0f020h]
 jne failed
 cmp word [{D['ARET']}],{0x3ff if flags&1 else 0}
 jne failed
 cmp byte [0f200h],{ord('F') if flags&1 else 229}
 jne failed
 cmp word [0f21ah],{7 if flags&1 else 0}
 jne failed
 cmp byte [0f20bh],{0x20|flags}
 jne failed
 cmp byte [0f010h],{0 if flags&1 else 1}
 jne failed
 cmp byte [0f011h],{0 if flags&1 else 1}
 jne failed
"""
        separate_near(code, C("DELETEF"), body)
        count += 1
print(
    f"PASS: {count} FAT delete exact/wildcard normal/SYSTEM/HIDDEN/combined and READ-ONLY cases"
)
