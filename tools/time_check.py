#!/usr/bin/env python3
"""Exercise TIME.EXE's exact display and prompt with a synthetic clock."""
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
COMMAND = ROOT / 'commands/datetime'


def check():
    exe = (COMMAND / 'time.exe').read_bytes()
    assert exe[:2] == b'MZ'
    size, pages, relocations, header, minimum, maximum, ss, sp, checksum, ip, cs, table = struct.unpack_from('<12H', exe, 2)
    length = (pages - 1) * 512 + size if size else pages * 512
    image = bytearray(exe[header * 16:length])
    for at in range(table, table + relocations * 4, 4):
        offset, segment = struct.unpack_from('<HH', exe, at)
        place = segment * 16 + offset
        value = struct.unpack_from('<H', image, place)[0]
        struct.pack_into('<H', image, place, (value + 0x2000) & 0xffff)
    cases = [(0,0,0,0), (1,2,3,4), (9,9,9,9), (10,16,58,0), (23,59,59,99)]
    with tempfile.TemporaryDirectory(prefix='cdos-time-') as td:
        folder=Path(td)
        (folder/'payload.bin').write_bytes(image)
        for h,m,s,hs in cases:
            (folder/'expected.bin').write_bytes(
                f'Current time is {h:02}:{m:02}:{s:02}.{hs:02}\r\nEnter new time: '.encode())
            values=dict(EXE_SS=ss+0x2000,EXE_SP=sp,EXE_IP=ip,EXE_CS=cs+0x2000,
                        TAIL_LEN=0,HOUR=h,MINUTE=m,SECOND=s,HUNDREDTH=hs)
            (folder/'case.inc').write_text(''.join(f'%define {n} {v}\n' for n,v in values.items()))
            subprocess.run(['nasm','-f','bin',str(COMMAND/'tests/timecheck.asm'),
                            '-I',str(folder)+'/', '-o',str(folder/'test.com')],check=True)
            result=subprocess.run(['emu2',str(folder/'test.com')],capture_output=True,timeout=5)
            assert result.returncode==0,(h,m,s,hs,result.stdout,result.stderr)
    print('PASS: five TIME.EXE exact display/prompt cases; no clock changed')

if __name__=='__main__':
    check()
