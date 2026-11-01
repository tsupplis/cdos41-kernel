#!/usr/bin/env python3
"""Compare 4.11/imported SDIR path parsing and current DOS subdirectories in PCE.

Requires PCE, mtools and cpmtools. The OEM binary is an executable oracle,
not a source/build dependency. Expected differences are documented beside
assertions; released images and host filesystems are never edited.
"""
from pathlib import Path
import re
import contextlib
import shutil
import subprocess
import tempfile
from alias_check import ROOT, MEDIA, run

PROMPT = 'Press any key to continue...'


@contextlib.contextmanager
def disposable_workspace():
    folder = tempfile.mkdtemp(prefix='cdos-sdir-')
    try:
        yield folder
    except BaseException:
        print('SDIR diagnostics retained in', folder, flush=True)
        raise
    else:
        shutil.rmtree(folder)


def check():
    for tool in ('pce-ibmpc', 'mformat', 'mcopy', 'mmd', 'mattrib', 'cpmcp'):
        assert shutil.which(tool), f'{tool} is required'
    with disposable_workspace() as td:
        folder = Path(td)
        def command(*args):
            return run(*args, cwd=folder)
        shutil.copyfile(MEDIA / 'diskdefs', folder / 'diskdefs')
        shutil.copyfile(MEDIA / 'cdos86.img', folder / 'cdos86.img')
        command('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2', '-n', '8', '-c', '2', '::')
        for src, name in [(ROOT / 'base/sdir.cmd', 'OSDIR.CMD'),
                          (ROOT / 'commands/sdir/sdir.cmd', 'NSDIR.CMD')]:
            command('mcopy', '-i', 'fat.img', str(src), '::' + name)
        fixtures = {'FZERO.TXT': b'', 'FONE.TXT': b'hello\r\n\x1a',
                    'FRO.TXT': b'read only\r\n', 'FSYS.TXT': b'system\r\n',
                    'FHIDDEN.TXT': b'hidden\r\n',
                    'KEYS.DAT': b'\r' * 32, 'STOP.DAT': b'\x03'}
        for i in range(30):
            fixtures[f'P{i:02}.TXT'] = b'paging fixture\r\n'
        for name, data in fixtures.items():
            (folder / name).write_bytes(data)
            command('mcopy', '-i', 'fat.img', name, '::' + name)
        for flag, name in [('+r', 'FRO.TXT'), ('+s', 'FSYS.TXT'), ('+h', 'FHIDDEN.TXT')]:
            command('mattrib', '-i', 'fat.img', flag, '::' + name)
        for name in ('FDIR1', 'FDIR2'):
            command('mmd', '-i', 'fat.img', '::' + name)
        command('mcopy', '-i', 'fat.img', 'FONE.TXT', '::FDIR1/CHILD.TXT')
        for name in ('OSDIR', 'NSDIR'):
            command('mcopy', '-i', 'fat.img', '::'+name+'.CMD', str(folder/(name+'.CMD')))
            command('mcopy', '-i', 'fat.img', str(folder/(name+'.CMD')), '::FDIR1/'+name+'.CMD')
        cfg = (MEDIA / 'cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder / 'cdos86.cfg').write_text(cfg)
        cases = [('', 'b:\\fdir1\\child.txt'), ('', 'b:fdir1\\child.txt'),
                 ('', 'b:\\missing\\*.txt'), ('', 'b:child.txt'),
                 ('size', 'b:child.txt'), ('', 'b:c*.txt'), ('', 'b:..\\fone.txt')]
        commands = ['c f000000']
        keys = {' ': 'Space', '\n': 'Return', '.': 'Period', '[': 'LeftBracket',
                ']': 'RightBracket', ',': 'Comma', '=': 'Equal',
                '*': '+Shift 8 -Shift', '?': '+Shift Slash -Shift',
                '\\': 'Backslash', '(': '+Shift 9 -Shift', ')': '+Shift 0 -Shift'}
        def type_command(text, label):
            for char in text + '\n':
                key = '+Shift Semicolon -Shift' if char == ':' else keys.get(char, char)
                commands.extend(['key ' + key, 'c 200000'])
            commands.extend(['c 4000000', f'save "{label}.bin" bin b800:0000 fa0'])
        for i, (option, spec) in enumerate(cases):
            if i == 3:
                type_command('chdir b:\\fdir1', 'chdir')
            tail = f' [{option}]' if option else ''
            for variant in ('O', 'N'):
                type_command(f'put [b:{variant}{i}.txt] b:{variant.lower()}sdir.cmd {spec}{tail}', f'{variant}{i}')
        commands.append('q')
        with (folder / 'pce.log').open('wb') as log:
            result = subprocess.run(['pce-ibmpc', '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                                    cwd=folder, input=('\n'.join(commands)+'\n').encode(),
                                    stdout=log, stderr=subprocess.STDOUT, timeout=600)
        assert result.returncode == 0, (folder / 'pce.log').read_text(errors='replace')[-2000:]
        def capture(label):
            screen = (folder / (label + '.bin')).read_bytes()
            lines = [''.join(chr(c) if 32 <= c < 127 else ' ' for c in screen[i:i+160:2]).strip()
                     for i in range(0, 3840, 160)]
            assert [s for s in lines if s][-1] == 'A>', (label, lines)
            prefix = '::FDIR1/' if int(label[1:]) >= 3 else '::'
            command('mcopy', '-o', '-i', 'fat.img', prefix+label+'.txt', str(folder / (label+'.txt')))
            return (folder / (label+'.txt')).read_bytes().rstrip(b'\x00\x1a').decode('ascii')
        def normalize(text, legacy=False):
            # 4.11 prints year-1900 with a single tens character: 2026 -> <6.
            # Normalize only that malformed original year, not rebuilt output.
            if legacy:
                text = re.sub(r'/([:;<=>?])([0-9])(?= )',
                              lambda m: '/' + f'{((ord(m[1])-48)*10+int(m[2])) % 100:02d}', text)
            # PUT creates a new log before each scan: physical dir usage differs
            # by one. DOS directory markers/counts are deliberate improvements.
            lines = [s for s in text.splitlines() if 'FDIR1' not in s and 'FDIR2' not in s]
            text = '\n'.join(lines)
            text = re.sub(r'Files Found =\s*\d+(  Directories Found =\s*\d+)?', 'Files Found = #', text)
            return re.sub(r'(Used/Max Dir Entries For Drive .:)\s*\d+/', r'\1 #/', text)
        for i, (option, spec) in enumerate(cases):
            old, new = capture('O'+str(i)), capture('N'+str(i))
            assert normalize(old, legacy=True) == normalize(new), (option, spec, old, new)
            if i in (0,1,2,6):
                assert 'Illegal command tail' in old and 'Illegal command tail' in new
            if i in (3,4,5):
                assert 'CHILD' in new and 'FONE' not in new, (spec,new)
        print('PASS: 7 original/rebuilt SDIR path/current-subdirectory comparisons')

if __name__ == '__main__':
    check()
