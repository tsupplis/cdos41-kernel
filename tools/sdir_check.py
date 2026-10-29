#!/usr/bin/env python3
"""Compare OEM/imported SDIR on disposable CP/M and FAT12 floppies in PCE.

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
        # CP/M fixtures: both a normal user and a nonzero user, plus RO.
        logical = folder / 'logical.img'
        twist = str(ROOT / 'tools/cpm86twist.py')
        command('python3', twist, 'untwist', 'cdos86.img', str(logical))
        for name, user in [('FONE.TXT', 0), ('FRO.TXT', 0), ('FONE.TXT', 1)]:
            command('cpmcp', '-f', 'ccpm86-320', str(logical), str(folder / name), f'{user}:' + name)
        disk = bytearray(logical.read_bytes())
        for at in range(4096, 6144, 32):
            if disk[at] == 0 and disk[at+1:at+12] == b'FRO     TXT':
                disk[at+9] |= 0x80
        logical.write_bytes(disk)
        command('python3', twist, 'twist', str(logical), 'cdos86.img')
        cfg = (MEDIA / 'cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder / 'cdos86.cfg').write_text(cfg)
        cases = [('', 'b:f*.*'), ('full', 'b:f*.*'), ('size', 'b:f*.*'),
                 ('date', 'b:f*.*'), ('dir', 'b:f*.*'), ('sys', 'b:f*.*'),
                 ('ro', 'b:f*.*'), ('rw', 'b:f*.*'), ('attrib', 'b:f*.*'),
                 ('nosort', 'b:f*.*'), ('sort', 'b:f*.*'), ('xfcb', 'b:f*.*'),
                 ('nonxfcb', 'b:f*.*'), ('user=0', 'b:f*.*'),
                 ('user=all', 'b:f*.*'), ('user=(0,1)', 'a:f*.*'),
                 ('g0', 'b:f*.*'), ('drive=b', 'f*.*'), ('disk=b', 'f*.*'),
                 ('length=5,ff', 'b:f*.*'), ('exclude', 'b:*.*'),
                 ('nonsense', 'b:f*.*'), ('length=4', 'b:f*.*'),
                 ('short', 'b:f*.*'), ('help', 'b:f*.*'),
                 ('', 'a:f*.*'), ('ro', 'a:f*.*')]
        commands = ['c f000000']
        keys = {' ': 'Space', '\n': 'Return', '.': 'Period', '[': 'LeftBracket',
                ']': 'RightBracket', ',': 'Comma', '=': 'Equal',
                '*': '+Shift 8 -Shift', '?': '+Shift Slash -Shift',
                '(': '+Shift 9 -Shift', ')': '+Shift 0 -Shift'}
        def type_command(text, label):
            for char in text + '\n':
                key = '+Shift Semicolon -Shift' if char == ':' else keys.get(char, char)
                commands.extend(['key ' + key, 'c 200000'])
            commands.extend(['c 4000000', f'save "{label}.bin" bin b800:0000 fa0'])
        for i, (option, spec) in enumerate(cases):
            tail = f' [{option}]' if option else ''
            for variant in ('O', 'N'):
                type_command(f'put [b:{variant}{i}.txt] b:{variant.lower()}sdir.cmd {spec}{tail}', f'{variant}{i}')
        for label, options, keysfile in [('page', 'page', 'keys'),
                                          ('nopage', 'page,nopage', 'keys'),
                                          ('stop', 'page', 'stop')]:
            type_command(f'rdr [b:{keysfile}.dat,b:{label}.txt] b:nsdir.cmd b:p*.* [{options}]', label)
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
            command('mcopy', '-o', '-i', 'fat.img', '::'+label+'.txt', str(folder / (label+'.txt')))
            return (folder / (label+'.txt')).read_bytes().rstrip(b'\x00\x1a').decode('ascii')
        def normalize(text):
            # PUT creates a new log before each scan: physical dir usage differs
            # by one. DOS directory markers/counts are deliberate improvements.
            lines = [s for s in text.splitlines() if 'FDIR1' not in s and 'FDIR2' not in s]
            text = '\n'.join(lines)
            text = re.sub(r'Files Found =\s*\d+(  Directories Found =\s*\d+)?', 'Files Found = #', text)
            return re.sub(r'(Used/Max Dir Entries For Drive .:)\s*\d+/', r'\1 #/', text)
        for i, (option, spec) in enumerate(cases):
            old, new = capture('O'+str(i)), capture('N'+str(i))
            if option == 'short':
                assert 'Illegal Option' in old and 'Illegal Option' not in new, new
                assert ':\\FDIR1' in new and ':\\FDIR2' in new, new
                for name in ('FZERO', 'FONE', 'FRO', 'FSYS', 'FHIDDEN'):
                    assert name in new, new
            elif option == 'help':
                assert 'Illegal Option' in old and 'SDIR [options]' in new, new
                assert 'SHORT' in new and 'PAGE NOPAGE HELP' in new, new
            elif option == 'size':
                assert new.count('<DIR>') == 2 and 'Files Found =    5' in new, new
                assert 'Directories Found =    2' in new, new
                for name in ('FZERO', 'FONE', 'FRO', 'FSYS', 'FHIDDEN'):
                    assert name in new, new
            else:
                assert normalize(old) == normalize(new), (option, spec, old, new)
                if spec == 'b:f*.*' and option in ('', 'full', 'date', 'dir', 'rw', 'attrib', 'nosort', 'sort', 'user=0', 'user=all', 'g0', 'length=5,ff', 'xfcb'):
                    assert new.count('<DIR>') == 2, (option, new)
                    assert 'Directories Found =    2' in new, (option, new)
                if spec.startswith('a:'):
                    assert '<DIR>' not in new, new
        page, nopage, stop = capture('page'), capture('nopage'), capture('stop')
        assert PROMPT in page and 'P29' in page, page
        assert PROMPT not in nopage and 'P29' in nopage, nopage
        assert PROMPT in stop and 'P29' not in stop, stop
        print(f'PASS: SDIR {len(cases)} OEM/rebuilt comparisons on CP/M/FAT12, directories, options, SHORT/HELP, paging/disable/Ctrl-C; disposable images only')


if __name__ == '__main__':
    check()
