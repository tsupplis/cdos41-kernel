#!/usr/bin/env python3
"""Exercise imported PUT/GET/RDR under 4.1 on disposable PCE images."""
from pathlib import Path
import shutil
import subprocess
import tempfile
from alias_check import ROOT, MEDIA, run


def check():
    emulator = shutil.which('pce-ibmpc')
    assert emulator, 'pce-ibmpc is required'
    with tempfile.TemporaryDirectory(prefix='cdos-redir-') as td:
        folder = Path(td)
        for name in ['cdos86.img', 'cdostools.img']:
            shutil.copyfile(MEDIA / name, folder / name)
        twist = str(ROOT / 'tools/cpm86twist.py')
        logical = folder / 'logical.img'
        payload = b''.join(f'redirected line {n:02}\r\n'.encode() for n in range(24))
        fixtures = [('text.txt', payload + b'\x1a'),
                    ('getin.dat', b'A:GOT.TXT=B:TEXT.TXT\r\n\r\n\x1a'),
                    ('rdrin.dat', b'A:RDRCOPY.TXT=B:TEXT.TXT\r\n\r\n\x1a')]
        run('python3', twist, 'untwist', str(folder / 'cdostools.img'), str(logical))
        for name, data in fixtures:
            p = folder / name
            p.write_bytes(data)
            run('cpmcp', '-f', 'ccpm86-320', str(logical), str(p), '0:' + name)
        run('python3', twist, 'twist', str(logical), str(folder / 'cdostools.img'))
        cfg = (MEDIA / 'cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        (folder / 'cdos86.cfg').write_text(cfg)
        commands = ['c f000000']
        names = {' ': 'Space', '\n': 'Return', '.': 'Period', '[': 'LeftBracket',
                 ']': 'RightBracket', ',': 'Comma'}
        cases = [('put', 'put [a:capture.txt] type.cmd b:text.txt\n'),
                 ('append', 'put [a:capture.txt,a] type.cmd b:text.txt\n'),
                 ('get', 'get [b:getin.dat] pip.cmd\n'),
                 ('rdr', 'rdr [b:rdrin.dat,a:session.log] pip.cmd\n')]
        for label, text in cases:
            for char in text:
                key = '+Shift Semicolon -Shift' if char == ':' else names.get(char, char)
                commands.extend(['key ' + key, 'c 200000'])
            commands.extend(['c 10000000', f'save "{label}.bin" bin b800:0000 fa0'])
        commands.append('q')
        with (folder / 'pce.log').open('wb') as log:
            p = subprocess.run([emulator, '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                               cwd=folder, input=('\n'.join(commands) + '\n').encode(),
                               stdout=log, stderr=subprocess.STDOUT, timeout=60)
        assert p.returncode == 0, (folder / 'pce.log').read_text(errors='replace')[-3000:]
        for label, _ in cases:
            data = (folder / (label + '.bin')).read_bytes()
            text = '\n'.join(''.join(chr(c) if 32 <= c < 127 else ' '
                                     for c in data[at:at + 160:2])
                             for at in range(0, 3840, 160))
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            assert lines[-1] == 'A>', (label, text)
            assert 'failed' not in text.lower() and 'Interrupt from' not in text, (label, text)
        run('python3', twist, 'untwist', str(folder / 'cdos86.img'), str(logical))
        for name in ['capture.txt', 'got.txt', 'rdrcopy.txt', 'session.log']:
            run('cpmcp', '-f', 'ccpm86-320', str(logical), '0:' + name, str(folder / name))
        def contents(name):
            return (folder / name).read_bytes().rstrip(b'\x00\x1a')
        assert contents('capture.txt') == payload * 2, 'PUT overwrite/append bytes differ'
        assert contents('got.txt') == payload, 'GET did not feed the PIP copy command'
        assert contents('rdrcopy.txt') == payload, 'RDR did not feed the PIP copy command'
        assert b'*' in contents('session.log'), 'RDR did not capture PIP output'
        print('PASS: 4.1 PUT multi-record output/append, GET input, RDR input/output and return to shell; disposable disks only')


if __name__ == '__main__':
    check()
