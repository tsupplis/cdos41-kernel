#!/usr/bin/env python3
"""Boot disposable CP/M and FAT images to test DOS country and file timestamps."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(os.environ.get('CDOS_TEST_ROOT', Path(__file__).resolve().parent.parent))


def check(cpm):
    with tempfile.TemporaryDirectory(prefix='cdos-stamp-') as temporary:
        folder = Path(temporary)

        def run(*args):
            return subprocess.run(args, cwd=folder, check=True, capture_output=True)

        shutil.copyfile(ROOT / 'media/cdos86.img', folder / 'cdos86.img')
        if cpm:
            twist = str(ROOT / 'tools/cpm86twist.py')
            run('python3', twist, 'untwist', 'cdos86.img', 'logical.img')
            image = bytearray((folder / 'logical.img').read_bytes())
            entries = [image[i:i+32] for i in range(4096, 6144, 32)
                       if image[i] != 0xe5]
            label = bytearray(32)
            label[0] = 0x20
            label[1:12] = b'STAMPTEST  '
            label[12] = 0x31
            entries.append(label)
            assert len(entries) < 48, 'Insufficient CP/M timestamp directory space'
            image[4096:6144] = b'\xe5' * 2048
            for i, entry in enumerate(entries):
                offset = 4096 + (i + i // 3) * 32
                image[offset:offset+32] = entry
            for i in range(3, 64, 4):
                image[4096+i*32:4096+(i+1)*32] = bytes([0x21]) + bytes(31)
            (folder / 'logical.img').write_bytes(image)
            run('python3', twist, 'twist', 'logical.img', 'cdos86.img')

        run('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2',
            '-n', '8', '-c', '2', '::')
        run('nasm', '-f', 'bin', str(ROOT / 'kernel/rsp3/tests/dos_stamp.asm'),
            '-D', f'CPM={int(cpm)}', '-o', 'stamp.com')
        run('mcopy', '-i', 'fat.img', 'stamp.com', '::')
        cfg = (ROOT / 'media/cdos86.cfg').read_text()
        cfg = cfg.replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder / 'cdos86.cfg').write_text(cfg)
        commands = ['c f000000']
        for char in 'b:stamp\n':
            key = {':': '+Shift Semicolon -Shift', '\n': 'Return'}.get(char, char)
            commands += ['key ' + key, 'c 200000']
        commands += ['c 4000000', 'save "result.bin" bin b800:0000 fa0', 'q']
        with (folder / 'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc', '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                           cwd=folder, input=('\n'.join(commands) + '\n').encode(),
                           stdout=log, stderr=log, timeout=60, check=True)
        video = (folder / 'result.bin').read_bytes()
        screen = '\n'.join(''.join(chr(v) if 32 <= v < 127 else ' '
                                   for v in video[i:i+160:2])
                           for i in range(0, 4000, 160))
        assert 'STAMP COUNTRY PASS' in screen, screen
    print('PASS: live ' + ('CP/M minute' if cpm else 'FAT two-second') +
          ' timestamps through write/set/duplicate/close/reopen, invalid handles/time, '
          'DOS 2.x country fields, reserved bytes and rejected selectors')


if __name__ == '__main__':
    check(False)
    check(True)
