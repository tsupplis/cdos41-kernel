#!/usr/bin/env python3
"""Exercise DATE.EXE's real parser with captured DOS date-setting calls."""
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
COMMAND = ROOT / 'commands/datetime'


def check():
    exe = (COMMAND / 'date.exe').read_bytes()
    assert exe[:2] == b'MZ'
    size, pages, relocations, header, minimum, maximum, ss, sp, checksum, ip, cs, table = struct.unpack_from('<12H', exe, 2)
    length = (pages - 1) * 512 + size if size else pages * 512
    image = bytearray(exe[header * 16:length])
    for at in range(table, table + relocations * 4, 4):
        offset, segment = struct.unpack_from('<HH', exe, at)
        place = segment * 16 + offset
        value = struct.unpack_from('<H', image, place)[0]
        struct.pack_into('<H', image, place, (value + 0x2000) & 0xffff)
    cases = [(f'1/2/{y:02}', 2000 + y if y < 78 else 1900 + y, 1, 2)
             for y in (0, 1, 19, 20, 26, 77, 78, 79, 80, 99)]
    cases += [(f'1/2/{y}', y, 1, 2) for y in (1978, 1980, 1999, 2000, 2019, 2020, 2026, 2077, 2099)]
    cases += [('2/29/00', 2000, 2, 29), ('2/29/2000', 2000, 2, 29)]
    cases += [(f'1/2/{y}', 0, 0, 0) for y in ('199', '200', '202', '20000', '2100', '26x')]
    count = 0
    with tempfile.TemporaryDirectory(prefix='cdos-date-') as td:
        folder = Path(td)
        (folder / 'payload.bin').write_bytes(image)
        for text, year, month, day in cases:
            for interactive in (False, True):
                tail = b'' if interactive else (' ' + text).encode('ascii')
                entry = text.encode('ascii') if interactive else b''
                (folder / 'tail.bin').write_bytes(tail)
                (folder / 'input.bin').write_bytes(entry)
                values = dict(EXE_SS=ss + 0x2000, EXE_SP=sp, EXE_IP=ip, EXE_CS=cs + 0x2000,
                              TAIL_LEN=len(tail), INPUT_LEN=len(entry), REJECT=int(not year),
                              EXPECT_YEAR=year, EXPECT_MONTH=month, EXPECT_DAY=day)
                (folder / 'case.inc').write_text(''.join(f'%define {name} {value}\n' for name, value in values.items()))
                subprocess.run(['nasm', '-f', 'bin', str(COMMAND / 'tests/datecheck.asm'),
                                '-I', str(folder) + '/', '-o', str(folder / 'test.com')], cwd=folder, check=True)
                result = subprocess.run(['emu2', str(folder / 'test.com')], cwd=folder,
                                        capture_output=True, timeout=5)
                assert result.returncode == 0, (text, 'interactive' if interactive else 'command line', result.stdout, result.stderr)
                count += 1
    print(f'PASS: {count} DATE.EXE parser cases (command line and interactive); no clock was changed')


if __name__ == '__main__':
    check()
