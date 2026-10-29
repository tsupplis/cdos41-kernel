#!/usr/bin/env python3
"""Check TMP/BATCH DEL and PAUSE on disposable 4.1 PCE disk copies."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / 'media'
PROMPT = 'Press any key to continue...'


def run(*args, cwd=MEDIA):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def check():
    emulator = shutil.which('pce-ibmpc')
    assert emulator, 'pce-ibmpc is required'
    with tempfile.TemporaryDirectory(prefix='cdos-alias-') as td:
        folder = Path(td)
        for name in ['cdos86.img', 'cdostools.img']:
            shutil.copyfile(MEDIA / name, folder / name)
        twist = str(ROOT / 'tools/cpm86twist.py')
        logical = folder / 'logical.img'
        run('python3', twist, 'untwist', str(folder / 'cdostools.img'), str(logical))
        for name, content in [('direct.txt', b'direct fixture\r\n\x1a'),
                              ('batch.txt', b'batch fixture\r\n\x1a'),
                              ('keep.txt', b'keep fixture\r\n\x1a'),
                              ('alias.bat', b'PAUSE\r\nDEL B:BATCH.TXT\r\n')]:
            p = folder / name
            p.write_bytes(content)
            run('cpmcp', '-f', 'ccpm86-320', str(logical), str(p), '0:' + name)
        run('python3', twist, 'twist', str(logical), str(folder / 'cdostools.img'))
        cfg = (MEDIA / 'cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        (folder / 'cdos86.cfg').write_text(cfg)
        commands = ['c f000000']

        def type_command(text):
            names = {' ': 'Space', '\n': 'Return', '.': 'Period'}
            for char in text:
                key = '+Shift Semicolon -Shift' if char == ':' else names.get(char, char)
                commands.extend(['key ' + key, 'c 200000'])
            commands.append('c 4000000')

        def save(name):
            commands.append(f'save "{name}.bin" bin b800:0000 fa0')

        def resume():
            commands.extend(['key Space', 'c 8000000'])

        type_command('pause\n')
        save('tmp-pause')
        resume()
        type_command('del b:direct.txt\n')
        save('direct')
        type_command('b:alias.bat\n')
        save('batch-pause')
        resume()
        save('batch-end')
        commands.append('q')
        with (folder / 'pce.log').open('wb') as log:
            p = subprocess.run([emulator, '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                               cwd=folder, input=('\n'.join(commands) + '\n').encode(),
                               stdout=log, stderr=subprocess.STDOUT, timeout=60)
        assert p.returncode == 0, (folder / 'pce.log').read_text(errors='replace')[-3000:]

        def screen(name):
            data = (folder / (name + '.bin')).read_bytes()
            return '\n'.join(''.join(chr(c) if 32 <= c < 127 else ' '
                                     for c in data[at:at + 160:2])
                             for at in range(0, 3840, 160))

        for name in ['tmp-pause', 'batch-pause']:
            lines = [line.rstrip() for line in screen(name).splitlines() if line.strip()]
            assert lines[-1].endswith(PROMPT), (name, screen(name))
        for name in ['direct', 'batch-end']:
            text = screen(name)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            assert lines[-1] == 'A>', (name, text)
            assert 'Error:' not in text and 'Interrupt from' not in text, (name, text)
        run('python3', twist, 'untwist', str(folder / 'cdostools.img'), str(logical))
        disk = logical.read_bytes()
        names = {bytes(c & 0x7f for c in disk[at + 1:at + 12])
                 for at in range(4096, 6144, 32) if disk[at] == 0}
        assert b'DIRECT  TXT' not in names, 'TMP DEL did not delete the named B: file'
        assert b'BATCH   TXT' not in names, 'BATCH DEL did not delete the named B: file'
        assert b'KEEP    TXT' in names, 'DEL affected an unrelated file'
        run('cpmcp', '-f', 'ccpm86-320', str(logical), '0:keep.txt', str(folder / 'kept.txt'))
        assert (folder / 'kept.txt').read_bytes().rstrip(b'\x00\x1a') == b'keep fixture\r\n'
        print('PASS: TMP and BATCH DEL invoke native ERA with B: arguments intact; unrelated file preserved; both PAUSE prompts match CCP/M 3.1')


if __name__ == '__main__':
    check()
