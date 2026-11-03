#!/usr/bin/env python3
"""Run the assembled BDOS 230 packet handler and FAT attribute backend.

Only disk selection, sector I/O, lock/error dependencies are stubbed.
The real packet validation, far FCB copy, lookup and masked writes execute.
"""

from historical_check import symbols, payload, run
from fat_recovery_check import hook, separate_near

D = symbols("pcbdos")
B = symbols("black")
base = symbols("bdos")["PCSEARCH"] - B["PCSEARCH"]
C = lambda n: base + B[n]

# operation, mask, value, original FAT attribute, expected native result,
# resulting attribute, expected writes, packet size/version/reserved, name/media
cases = []
for attr in [0, 1, 2, 4, 6, 0x20, 0x27, 0x60]:
    cases += [(1, 0, 0, attr, 0, attr, 0, 16, 1, 0, "FILE    TXT", 1)]
    for value in [0, 2]:
        new = (attr & ~2) | value
        cases += [
            (2, 2, value, attr, 0, new, int(new != attr), 16, 1, 0, "FILE    TXT", 1)
        ]
for mask, value in [(1, 1), (4, 4), (0x20, 0), (0x27, 0x27), (0, 0xFF)]:
    new = (0x22 & ~mask) | (value & mask)
    cases += [
        (2, mask, value, 0x22, 0, new, int(new != 0x22), 16, 1, 0, "FILE    TXT", 1)
    ]
cases += [
    (0, 0, 0, 0, 0, 0, 0, 16, 1, 0, "FILE    TXT", 0),
    (1, 0, 0, 0, 0x81FF, 0, 0, 16, 1, 0, "FILE    TXT", 0),
    (1, 0, 0, 8, 0x82FF, 8, 0, 16, 1, 0, "FILE    TXT", 1),
    (1, 0, 0, 16, 0x84FF, 16, 0, 16, 1, 0, "FILE    TXT", 1),
    (2, 2, 2, 16, 0x84FF, 16, 0, 16, 1, 0, "FILE    TXT", 1),
    (1, 0, 0, 0, 0x82FF, 0, 0, 16, 1, 0, "ABSENT  TXT", 1),
    (1, 0, 0, 0, 0x83FF, 0, 0, 16, 1, 0, "?ILE    TXT", 1),
    (1, 0, 0, 0, 0x83FF, 0, 0, 16, 1, 0, "*ILE    TXT", 1),
    (1, 0, 0, 0, 0x83FF, 0, 0, 16, 1, 0, "           ", 1),
    (1, 0, 0, 0, 0x80FF, 0, 0, 14, 1, 0, "FILE    TXT", 1),
    (1, 0, 0, 0, 0x80FF, 0, 0, 16, 2, 0, "FILE    TXT", 1),
    (1, 0, 0, 0, 0x80FF, 0, 0, 16, 1, 1, "FILE    TXT", 1),
    (3, 0, 0, 0, 0x80FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
    (2, 8, 8, 0, 0x80FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
    (2, 16, 16, 0, 0x80FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
    (2, 0x100, 0, 0, 0x80FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
    (2, 2, 0x100, 0, 0x80FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
]
cases += [
    (2, 2, 2, 0, 0x02FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
    (2, 2, 2, 0, 0x05FF, 0, 0, 16, 1, 0, "FILE    TXT", 1),
]
edges = {
    "PKTWRAP TXT": f"mov word [{D['INFO']}],0fff1h\n",
    "FCBWRAP TXT": "mov word [es:0e106h],0fff5h\n",
    "BADDRV  TXT": "mov byte [es:0e000h],17\n",
    "CAPSANY TXT": "mov word [es:0e106h],0ffffh\nmov word [es:0e108h],0ffffh\n",
}
for name, status, operation in [
    ("PKTWRAP TXT", 0x80FF, 1),
    ("FCBWRAP TXT", 0x83FF, 1),
    ("BADDRV  TXT", 0x83FF, 1),
    ("CAPSANY TXT", 0, 0),
]:
    cases.append((operation, 0, 0, 0, status, 0, 0, 16, 1, 0, name, 1))
for (
    op,
    mask,
    value,
    attr,
    status,
    result,
    writes,
    size,
    version,
    reserved,
    name,
    media,
) in cases:
    code = bytearray(payload("bdos"))
    hook(code, D["RESELECTX"], f'mov byte [{D["MEDIA_FORMAT"]}],{media}\nret')
    hook(
        code,
        D["RD_PCDIR"],
        f"""inc word [{D['DCNT']}]
 cmp word [{D['DCNT']}],1
 jae done
 mov ax,0f200h
 ret
done:
 xor ax,ax
 ret
""",
    )
    for symbol, source in [
        (
            "CHECKWRITE",
            f"mov word [{D['ARET']}],02ffh\npop ax\nret" if status == 0x02FF else "ret",
        ),
        (
            "CHK_OLIST",
            f"mov word [{D['ARET']}],05ffh\npop ax\nret" if status == 0x05FF else "ret",
        ),
        ("WRDIR", "inc byte [0f010h]\nret"),
        ("FLUSH", "inc byte [0f011h]\nret"),
    ]:
        hook(code, D[symbol], source)
    body = f"""mov ax,ds
 sub ax,1000h
 mov es,ax
 mov [{D['PARAMETERSEGMENT']}],ax
 mov word [{D['INFO']}],0e100h
 mov word [{D['ARET']}],0
 mov word [0f010h],0
 mov word [{D['HDSADDR']}],0f100h
 mov word [0f012h],0beefh
 mov word [es:0e100h],{size}
 mov word [es:0e102h],{version}
 mov word [es:0e104h],{op}
 mov word [es:0e106h],0e000h
 mov word [es:0e108h],ax
 mov word [es:0e10ah],{mask}
 mov word [es:0e10ch],{value}
 mov word [es:0e10eh],{reserved}
 mov byte [es:0e000h],2
"""
    for i, v in enumerate(name.encode()):
        body += f"mov byte [es:{0xe001+i}],{v}\n"
    record = b"FILE    TXT" + bytes([attr, 0x18]) + bytes(range(13, 32))
    for i, v in enumerate(record):
        body += f"mov byte [{0xf200+i}],{v}\n"
    body += edges.get(name, "")
    body += f"""mov [0f020h],sp
 call far [cs:target]
 mov ax,[{D['PARAMETERSEGMENT']}]
 mov es,ax
 cmp sp,[0f020h]
 jne failed
 cmp word [{D['ARET']}],{status}
 jne failed
 cmp byte [0f010h],{writes}
 jne failed
 cmp byte [0f011h],{writes}
 jne failed
 cmp byte [0f20bh],{result}
 jne failed
 cmp word [0f012h],0beefh
 jne failed
"""
    for i, v in enumerate(record):
        if i != 11:
            body += f"cmp byte [{0xf200+i}],{v}\njne failed\n"
    for i, v in enumerate(name.encode()):
        body += f"cmp byte [es:{0xe001+i}],{v}\njne failed\n"
    if status == 0:
        body += f"cmp word [es:0e10ah],27h\njne failed\ncmp word [es:0e10ch],{0x4146 if op==0 else result}\njne failed\n"
    checks = []
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if "jne failed" in line:
            checks.append(lines[i - 1])
            lines[i] = line.replace("jne failed", f"jne check_failed_{len(checks)}")
    body = "\n".join(lines) + "\njmp checks_done\n"
    for i, check in enumerate(checks, 1):
        body += f"check_failed_{i}: mov ax,{0x4c00+i}\nint 21h\n"
    body += "checks_done:\n"
    try:
        separate_near(code, D["FUNC230"], body)
    except AssertionError as exc:
        raise AssertionError(
            (op, mask, value, attr, status, name, checks, exc)
        ) from exc
print(
    f"PASS: {len(cases)} BDOS 230 assembled capabilities/get/masked-set, far FCB, metadata preservation, media and validation cases"
)

# Verify normalization after common BDOS cleanup: AX/BX/CX, not CF.
for native, reason in [
    (0, 0),
    (0x80FF, 0x80),
    (0x81FF, 0x81),
    (0x82FF, 0x82),
    (0x83FF, 0x83),
    (0x84FF, 0x84),
    (0x02FF, 2),
    (0x05FF, 5),
]:
    code = bytearray(payload("bdos"))
    hook(code, D["GETDISKMX"], f"mov bx,{native}\nmov cx,0beefh\nret")
    run(
        code,
        D["FATATTR_ENTRY"],
        f"""call far [cs:target]
 cmp ax,{0 if native==0 else 0xffff}
 jne failed
 cmp bx,ax
 jne failed
 cmp cx,{reason}
 jne failed
""",
    )
print("PASS: eight BDOS 230 AX/BX/CX status normalization cases")
