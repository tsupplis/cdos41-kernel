#!/usr/bin/env python3
"""Test the built XIOS cursor detector against BIOS/font-height fixtures."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CON = ROOT / 'kernel/con'


def check():
    symbols = dict((name, int(value, 16)) for value, name in
                   re.findall(r'\b([0-9A-F]{4})\s+([A-Z][A-Z0-9]*)',
                              (CON / 'squid.sym').read_text()))
    image = (CON / 'xios.con').read_bytes()
    length = int.from_bytes(image[1:3], 'little') * 16
    code = bytearray(image[128:128 + length])
    # The detector returns near; a CALL/RETF trampoline in the unused
    # SYSDAT prefix lets the harness enter/leave its actual code segment.
    code[:4] = b'\xe8' + ((symbols['DETECTCURSOR'] - 3) & 0xffff).to_bytes(2, 'little') + b'\xcb'
    count = 0
    with tempfile.TemporaryDirectory(prefix='cdos-cursor-') as td:
        folder = Path(td)
        (folder / 'payload.bin').write_bytes(code)
        for adapter, height, port in [(0xff, 8, 0x3d4), (0xff, 16, 0x3b4),
                                      (0, 8, 0x3d4), (0, 14, 0x3d4),
                                      (0, 16, 0x3d4), (0, 32, 0x3d4),
                                      (1, 14, 0x3b4), (1, 16, 0x3b4),
                                      (0, 0, 0x3d4), (0, 7, 0x3d4),
                                      (0, 33, 0x3d4), (0, 16, 0x3ba),
                                      (2, 16, 0x3d4)]:
            valid = adapter <= 1 and 8 <= height <= 32 and port in (0x3d4, 0x3b4)
            cursor = ((height - 2) << 8) | (height - 1) if valid else 0
            values = dict(VAR_CURSOR=symbols['VARCURSOR'], VAR_MONO=symbols['VARMONOCURSOR'],
                          VAR_SYNC=symbols['VARSYNC'], ADAPTER=adapter, HEIGHT=height,
                          CRT_PORT=port, EXPECT_COLOR=cursor if valid and port == 0x3d4 else 0x607,
                          EXPECT_MONO=cursor if valid and port == 0x3b4 else 0xb0c,
                          EXPECT_SYNC=0 if valid and port == 0x3d4 else 8)
            (folder / 'case.inc').write_text(''.join(f'%define {key} {value}\n' for key, value in values.items()))
            subprocess.run(['nasm', '-f', 'bin', str(CON / 'tests/cursorcheck.asm'),
                            '-I', str(folder) + '/', '-o', str(folder / 'test.com')], cwd=folder, check=True)
            p = subprocess.run(['emu2', str(folder / 'test.com')], cwd=folder,
                               capture_output=True, timeout=5)
            assert p.returncode == 0, (adapter, height, hex(port), p.stdout, p.stderr)
            count += 1
    print(f'PASS: {count} built-XIOS cursor cases: EGA/VGA heights, monochrome, legacy and invalid probes')


if __name__ == '__main__':
    check()
