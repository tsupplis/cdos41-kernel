#!/usr/bin/env python3
"""Boot disposable media and exercise recovered DOS services with real loaders."""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(os.environ.get('CDOS_TEST_ROOT', Path(__file__).resolve().parent.parent))


def check():
    with tempfile.TemporaryDirectory(prefix='cdos-pctmp-') as td:
        folder = Path(td)

        def run(*args):
            subprocess.run(args, cwd=folder, check=True, capture_output=True)

        shutil.copyfile(ROOT / 'media/cdos86.img', folder / 'cdos86.img')
        run('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2', '-n', '8', '-c', '2', '::')
        run('mlabel', '-i', 'fat.img', '::VERIFY')
        boot = (folder / 'fat.img').read_bytes()[:512]
        w = lambda i: int.from_bytes(boot[i:i+2], 'little')
        clusters = (w(19)-w(14)-boot[16]*w(22)-(w(17)*32+w(11)-1)//w(11))//boot[13]
        run('nasm', '-f', 'bin', str(ROOT / 'kernel/rsp3/tests/pctmp_recovery.asm'), '-D', f'FATCLUSTERS={clusters}', '-o', 'recover.com')
        # Deliberately unexecuted signatures: the parent checks the returned
        # CS:IP against these bytes. The EXE has a 32-byte MZ header, no relocs.
        signature = b'\x5a\xa5\xcd\x20'
        (folder / 'child.com').write_bytes(signature)
        header = struct.pack('<14H', 0x5a4d, 36, 1, 0, 2, 0x100,
                             0xffff, 0, 0x1000, 0, 0, 0, 28, 0) + bytes(4)
        (folder / 'child.exe').write_bytes(header + signature)
        for name in ['recover.com', 'child.com', 'child.exe']:
            run('mcopy', '-i', 'fat.img', name, '::')
        run('mmd', '-i', 'fat.img', '::OPENED', '::OTHER')
        (folder / 'saved.dat').write_bytes(b'Q')
        for directory in ['OPENED', 'OTHER']:
            run('mcopy', '-i', 'fat.img', 'saved.dat', '::'+directory+'/SAVED.DAT')
        cfg = (ROOT / 'media/cdos86.cfg').read_text()
        cfg = cfg.replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder / 'cdos86.cfg').write_text(cfg)
        commands = ['c f000000']
        for char in 'b:recover\n':
            key = {':': '+Shift Semicolon -Shift', '\n': 'Return'}.get(char, char)
            commands += ['key ' + key, 'c 200000']
        commands += ['c 4000000']
        for key in ['a', 'b', 'c', 'Return']:
            commands += ['key '+key, 'c 200000']
        commands += ['c 4000000', 'save "result.bin" bin b800:0000 fa0', 'q']
        with (folder / 'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc', '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                           cwd=folder, input=('\n'.join(commands) + '\n').encode(),
                           stdout=log, stderr=log, timeout=60, check=True)
        video = (folder / 'result.bin').read_bytes()
        text = '\n'.join(''.join(chr(v) if 32 <= v < 127 else ' '
                                 for v in video[i:i+160:2]) for i in range(0, 4000, 160))
        assert 'RECOVERY LIVE PASS' in text, text
        for name, content in [('growa.dat', b'Z'), ('growb.dat', b'Y')]:
            run('mcopy', '-i', 'fat.img', '::'+name, name)
            assert (folder / name).read_bytes() == content * (64 * 512), name
        for directory, expected in [('OPENED', b'K'*128), ('OTHER', b'Q')]:
            run('mcopy', '-o', '-i', 'fat.img', '::'+directory+'/SAVED.DAT', 'saved.dat')
            assert (folder / 'saved.dat').read_bytes() == expected, directory
    print('PASS: PCE DOS PSP stub, 50h/51h, real COM/EXE 4B01h loads, entry-point contents, child memory release return to shell; FAT12/CPM geometry, drive restoration, volume-label masks/find-next, zero/bounded console input; interleaved 32-KiB FAT file growth; FCB close after CHDIR (written/unwritten), restored directory and both files verified byte-for-byte')


if __name__ == '__main__':
    check()
