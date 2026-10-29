#!/usr/bin/env python3
"""Compare the retained Concurrent 3.2 TYPE with the maintained source build."""
from pathlib import Path
import contextlib
import shutil
import subprocess
import tempfile
import sys
from alias_check import ROOT, MEDIA, run

PROMPT = b'Press any key to continue...'


@contextlib.contextmanager
def workspace():
    name = tempfile.mkdtemp(prefix='cdos-type-')
    try:
        yield Path(name)
    except BaseException:
        print('TYPE diagnostics retained in', name, flush=True)
        raise
    else:
        shutil.rmtree(name)


def check(passwords=False, large=False):
    for tool in ('pce-ibmpc', 'mformat', 'mcopy', 'mmd', 'cpmcp'):
        assert shutil.which(tool), f'{tool} is required'
    with workspace() as folder:
        def command(*args):
            return run(*args, cwd=folder)
        shutil.copyfile(MEDIA / 'diskdefs', folder / 'diskdefs')
        shutil.copyfile(MEDIA / 'cdos86.img', folder / 'cdos86.img')
        command('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2', '-n', '8', '-c', '2', '::')
        for source, name in [(ROOT / 'base/type.cmd', 'OTYPE.CMD'),
                              (ROOT / 'commands/type/type.cmd', 'NTYPE.CMD')]:
            command('mcopy', '-i', 'fat.img', str(source), '::'+name)
        fixtures = {'EMPTY.TXT': b'', 'SHORT.TXT': b'first line\r\nsecond line\x1a',
                    'CR.TXT': b'first\rsecond\r\x1a', 'LF.TXT': b'first\nsecond\n\x1a',
                    'EOF.TXT': b'before\x1aafter\r\n', 'RAW.TXT': b'no final line ending',
                    'BLOCK.TXT': b'Q'*128, 'CROSS.TXT': b'A'*127+b'\x1aBAD',
                    'CONTROL.TXT': b'\x00\x01\x08\t\r\n\x1b\x7f$\xff\x1a',
                    'LONG.TXT': b''.join(f'line {i:02}\r\n'.encode() for i in range(35))+b'\x1a',
                    'EXACT.TXT': b''.join(f'exact {i:02}\r\n'.encode() for i in range(23))+b'\x1a',
                    'WRAP.TXT': (b'wrap\t'+b'x'*90+b'\r\n')*20+b'\x1a',
                    'KEYS.DAT': b'\r'*64, 'STOP.DAT': b'\x03'}
        if large: fixtures['LARGE.TXT'] = b'L'*65536+b'Z'
        if passwords:
            fixtures.update({'SECRET.TXT': b'protected payload\r\n\x1a',
                             'PASS.DAT': b'secret\r', 'WRONG.DAT': b'wrong\r',
                             'EDIT.DAT': b'secrex\x08t\r',
                             'KILL.DAT': b'bad\x18secret\r', 'CANCEL.DAT': b'\x03'})
        for name, data in fixtures.items():
            (folder / name).write_bytes(data)
            command('mcopy', '-i', 'fat.img', name, '::'+name)
        command('mmd', '-i', 'fat.img', '::ADIR')
        # CP/M tests intentionally use small fixtures; only record padding is added.
        twist = str(ROOT / 'tools/cpm86twist.py')
        command('python3', twist, 'untwist', 'cdos86.img', 'logical.img')
        for name in (('SECRET.TXT',) if passwords else ('SHORT.TXT', 'EOF.TXT', 'CR.TXT')):
            command('cpmcp', '-f', 'ccpm86-320', 'logical.img', name, '0:'+name)
        command('python3', twist, 'twist', 'logical.img', 'cdos86.img')
        cfg = (MEDIA / 'cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder / 'cdos86.cfg').write_text(cfg)
        cases = [('b:'+name.lower(), name) for name in
                 ('EMPTY.TXT', 'SHORT.TXT', 'CR.TXT', 'LF.TXT', 'EOF.TXT', 'RAW.TXT',
                  'BLOCK.TXT', 'CROSS.TXT', 'CONTROL.TXT', 'LONG.TXT')]
        cases += [('b:missing.txt', None), ('b:*.txt', None), ('b:adir', None),
                  ('', None), ('b:short.txt;secret', 'SHORT.TXT'),
                  ('a:short.txt', 'SHORT.TXT'), ('a:eof.txt', 'EOF.TXT'),
                  ('a:cr.txt', 'CR.TXT'), ('b:long.txt p03', 'legacy'),
                  ('b:long.txt p', 'legacy')]
        if large: cases = [('b:large.txt', 'LARGE.TXT')]
        if passwords:
            cases = [('a:secret.txt;secret', 'secret'), ('a:secret.txt', 'secret'),
                     ('a:secret.txt', 'secret'), ('a:secret.txt', 'secret'),
                     ('a:secret.txt', 'wrong'), ('a:secret.txt;wrong', 'secret'),
                     ('a:secret.txt', 'cancel')]
        commands = ['c f000000']
        keynames = {' ': 'Space', '.': 'Period', '[': 'LeftBracket', ']': 'RightBracket',
                    ',': 'Comma', '*': '+Shift 8 -Shift', ';': 'Semicolon'}
        def type_command(text, label):
            for char in text:
                key = '+Shift Semicolon -Shift' if char == ':' else keynames.get(char, char)
                commands.extend(['key '+key, 'c 200000'])
            commands.extend(['key Return', 'c 20000000' if large else 'c 4000000', f'save "{label}.bin" bin b800:0000 fa0'])
        if passwords:
            keynames.update({'=': 'Equal'})
            type_command('set a: [protect=on]', 'enable')
            type_command('set a:secret.txt [password=secret,protect=read]', 'setup')
        for i, (tail, _) in enumerate(cases):
            for variant in ('O', 'N'):
                keysfile = (['keys', 'pass', 'edit', 'kill', 'wrong', 'pass', 'cancel'][i] if passwords else 'keys')
                type_command(f'rdr [b:{keysfile}.dat,b:{variant}{i}.txt] b:{variant.lower()}type.cmd {tail}', f'{variant}{i}')
        extras = [('page', 'b:long.txt [page]', 'keys'),
                  ('exact', 'b:exact.txt [page]', 'keys'),
                  ('wrap', 'b:wrap.txt [page]', 'keys'),
                  ('stop', 'b:long.txt [page]', 'stop'),
                  ('badopt', 'b:short.txt [bogus]', 'keys'),
                  ('p10', 'b:long.txt [p10]', 'keys'),
                  ('p23', 'b:long.txt [p23]', 'keys'),
                  ('p01', 'b:short.txt [p01]', 'keys'),
                  ('bad00', 'b:short.txt [p00]', 'keys'),
                  ('bad24', 'b:short.txt [p24]', 'keys'),
                  ('badp', 'b:short.txt [p]', 'keys')]
        if passwords or large: extras = []
        for label, tail, keys in extras:
            type_command(f'rdr [b:{keys}.dat,b:x{label}.txt] b:ntype.cmd {tail}', label)
        commands.append('q')
        with (folder / 'pce.log').open('wb') as log:
            result = subprocess.run(['pce-ibmpc', '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                                    cwd=folder, input=('\n'.join(commands)+'\n').encode(),
                                    stdout=log, stderr=subprocess.STDOUT, timeout=600)
        assert not result.returncode, (folder / 'pce.log').read_text(errors='replace')[-2000:]
        def capture(label):
            b = (folder / (label+'.bin')).read_bytes()
            rows = [''.join(chr(c) if 32<=c<127 else ' ' for c in b[i:i+160:2]).strip()
                    for i in range(0,3840,160)]
            assert [s for s in rows if s][-1] == 'A>', (label, rows)
            diskname = label if label[0] in ('O','N') else 'x'+label
            destination = folder / ('capture-'+label+'.txt')
            command('mcopy', '-o', '-i', 'fat.img', '::'+diskname+'.txt', str(destination))
            # Output captures end with Ctrl-Z padding, and fixtures never emit Ctrl-Z.
            return destination.read_bytes().rstrip(b'\x1a')
        for i, (tail, expected) in enumerate(cases):
            old, new = capture('O'+str(i)), capture('N'+str(i))
            if passwords:
                assert old == new, (tail, old, new)
                payload = fixtures['SECRET.TXT'][:-1]
                if expected == 'secret':
                    assert new.endswith(payload), (i, tail, new)
                    if i != 0: assert b'Password ?' in new, (i, new)
                else:
                    assert payload not in new and b'Password ?' in new, (i,new)
            elif expected in ('RAW.TXT', 'LARGE.TXT'):
                # OEM TYPE emits the kernel's zero-filled remainder of the
                # final DOS record; 4.1 adaptation honors the exact byte length.
                wanted = fixtures[expected]
                assert old == wanted.ljust((len(wanted)+127)//128*128,b'\x00'), (tail,len(old),len(wanted))
                assert new == wanted, new
            elif expected == 'legacy':
                assert b'line 34' in old and b'Invalid option' in new, (tail,old,new)
                assert b'line 00' not in new, new
            else:
                assert old == new, (tail, old, new)
                if expected:
                    wanted = fixtures[expected].split(b'\x1a',1)[0]
                    assert new == wanted, (tail, new, wanted)
        if large:
            print('PASS: TYPE exact DOS length across the 65536-byte boundary; OEM emits record padding, adapted TYPE stops at 65537 bytes')
            return
        if passwords:
            print(f'PASS: TYPE {len(cases)} OEM/rebuilt protected-file cases: inline/prompted password, Backspace, Ctrl-X, wrong password and Ctrl-C')
            return
        def without_page(text):
            return text.replace(PROMPT+b'\r'+b' '*28+b'\r', b'')
        outputs = {label: capture(label) for label,_,_ in extras}
        page, exact, wrap, stop, badopt = (outputs[label] for label in ('page','exact','wrap','stop','badopt'))
        assert PROMPT in page and without_page(page) == fixtures['LONG.TXT'][:-1], page
        assert PROMPT not in exact and exact == fixtures['EXACT.TXT'][:-1], exact
        assert PROMPT in wrap and without_page(wrap) == fixtures['WRAP.TXT'][:-1], wrap
        assert PROMPT in stop and b'line 34' not in stop, stop
        assert b'Invalid option' in badopt and b'first line' not in badopt, badopt
        for label, count, name in [('p10',3,'LONG.TXT'),('p23',1,'LONG.TXT'),('p01',1,'SHORT.TXT')]:
            text=outputs[label]
            assert text.count(PROMPT)==count and without_page(text)==fixtures[name][:-1], (label,text)
        for label in ('bad00','bad24','badp'):
            assert b'Invalid option' in outputs[label] and b'first line' not in outputs[label], (label,outputs[label])
        print(f'PASS: TYPE {len(cases)} OEM/rebuilt comparisons on CP/M/FAT12, text/EOF/errors, old P/PNN rejection, PAGE/P01..P23/wrap/exact-boundary/Ctrl-C; disposable images only')


if __name__ == '__main__':
    check('--passwords' in sys.argv, '--large' in sys.argv)
