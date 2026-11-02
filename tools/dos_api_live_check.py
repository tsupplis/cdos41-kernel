#!/usr/bin/env python3
"""Exercise local DOS APIs and Ctrl-C on disposable PCE media."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(os.environ.get('CDOS_TEST_ROOT', Path(__file__).resolve().parent.parent))


def check(cpm=False, interrupt=False):
    with tempfile.TemporaryDirectory(prefix='cdos-api-') as temporary:
        folder = Path(temporary)

        def run(*args):
            return subprocess.run(args, cwd=folder, check=True, capture_output=True)

        shutil.copyfile(ROOT / 'media/cdos86.img', folder / 'cdos86.img')
        run('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2',
            '-n', '8', '-c', '2', '::')
        name = 'dos_break.asm' if interrupt else 'dos_api.asm'
        run('nasm', '-f', 'bin', str(ROOT / 'kernel/rsp3/tests' / name),
            '-D', f'CPM={int(cpm)}', '-o', 'apicheck.com')
        run('mcopy', '-i', 'fat.img', 'apicheck.com', '::')
        cfg = (ROOT / 'media/cdos86.cfg').read_text()
        cfg = cfg.replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder / 'cdos86.cfg').write_text(cfg)
        commands = ['c f000000']
        for char in 'b:apicheck\n':
            key = {':': '+Shift Semicolon -Shift', '\n': 'Return'}.get(char, char)
            commands += ['key ' + key, 'c 200000']
        commands += ['c 4000000']
        if interrupt:
            commands += ['key +Ctrl', 'c 100000', 'key c', 'c 200000',
                         'key -Ctrl', 'c 4000000']
        commands += ['save "result.bin" bin b800:0000 fa0', 'q']
        with (folder / 'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc', '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                           cwd=folder, input=('\n'.join(commands) + '\n').encode(),
                           stdout=log, stderr=log, timeout=60, check=True)
        video = (folder / 'result.bin').read_bytes()
        screen = '\n'.join(''.join(chr(v) if 32 <= v < 127 else ' '
                                   for v in video[i:i+160:2])
                           for i in range(0, 4000, 160))
        expected = 'DOS BREAK PASS' if interrupt else 'DOS FIVE PASS'
        assert expected in screen, screen
        if not interrupt and not cpm:
            run('mcopy', '-i', 'fat.img', '::APIFIVE.DAT', 'result.dat')
            assert (folder / 'result.dat').read_bytes() == b'X' * 130 + b'END'
    print('PASS: live ' + ('application INT 23h delivery and user registers' if interrupt
          else ('CP/M' if cpm else 'FAT') +
          ' readiness, duplicate-handle commit, continued I/O, exact reopened size, verification setting and extended errors'))


if __name__ == '__main__':
    check()
    check(cpm=True)
    check(interrupt=True)
