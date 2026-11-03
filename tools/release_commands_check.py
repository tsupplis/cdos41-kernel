"""Compare OEM and rebuilt commands in disposable CDOS/PCE sessions."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = {'eraq': 'era/eraq.cmd', 'pip': 'pip/pip4.cmd',
         'path': 'path/path.cmd', 'date': 'datetime/date.exe'}
CLI = ['chset', 'eraq', 'pip', 'dsp', 'printmgr', 'path', 'date']
KEYS = {' ': 'Space', ':': '+Shift Semicolon -Shift', ';': 'Semicolon',
        '.': 'Period', '[': 'LeftBracket', ']': 'RightBracket', '=': 'Equal',
        ',': 'Comma', '+': '+Shift Equal -Shift', '/': 'Slash',
        '*': '+Shift 8 -Shift', '\\': 'Backslash'}

# Each step sends a shell command, optional interactive keys and saves the screen.
# A blank command continues inside the application.
CASES = {
    'cli': [
        ('b:chset b:sample.cmd', []), ('b:chset b:sample.cmd [shared=on]', []),
        ('b:chset b:sample.cmd [8087=opt,suspend=on]', []),
        ('b:chset b:sample.cmd [shared=off,shared=on]', []),
        ('b:chset b:sample.cmd', []), ('b:chset b:missing.cmd', []),
        ('b:eraq b:keep.txt', ['n']), ('b:eraq b:gone.txt', ['y']),
        ('b:eraq b:missing.txt', []), ('b:pip b:out.txt=b:keep.txt[v]', []),
        ('b:pip b:joined.txt=b:keep.txt,b:keep.txt', []),
        ('b:pip b:none.txt=b:missing.txt', []), ('b:dsp', []), ('b:dsp', []),
        ('b:printmgr badoption', []), ('b:printmgr', []),
        ('b:printmgr status', []), ('b:path b:\\alpha;b:\\beta', []),
        ('b:path', []), ('b:path ;', []), ('b:path', []),
        ('b:date 12/31/1999', []), ('b:date', ['Return']), ('b:pip', []), ('', ['Return'])],
    'copymenu': [('b:', []), ('copymenu', []),
                 ('', list('missing') + ['Return']), ('', ['Esc'])],
    'editmenu': [('b:', []), ('editmenu', []), ('', ['F1']),
                 ('', list('sample')), ('', ['Esc']), ('', ['Esc'])],
    'dredix': [('b:', []), ('dredix keep.txt', []), ('', list('xyz')),
               ('', ['+Alt h -Alt']), ('', ['Space'])],
    'function': [('b:function', []), ('', ['Return']), ('', ['F2']), ('', ['Esc'])],
    'help': [('b:', []), ('help', []), ('', list('dir') + ['Return']),
             ('', ['Esc']), ('', ['Esc'])],
    'batch': [('b:', []), ('batch test', [])],
}


def session(work, group, variant):
    folder = work / (group + '-' + variant)
    folder.mkdir()

    def run(*args):
        return subprocess.run(args, cwd=folder, capture_output=True, check=True)

    def put(path, name):
        run('mcopy', '-i', 'fat.img', str(path), '::' + name)

    shutil.copyfile(ROOT / 'media/cdos86.img', folder / 'cdos86.img')
    config = (ROOT / 'media/cdos86.cfg').read_text()
    config = config.replace('driver = "sdl"', 'driver = "null"')
    config = config.replace('sdl:lowpass=5000', 'null').replace('cdostools.img', 'fat.img')
    (folder / 'cfg').write_text(config)
    run('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2', '-n', '8', '-c', '2', '::')
    for name in CLI if group == 'cli' else [group]:
        filename = name + ('.exe' if name == 'date' or (name == 'path' and variant == 'original') else '.cmd')
        binary = ROOT / 'base' / filename if variant == 'original' else (
            ROOT / 'commands' / TOOLS.get(name, name + '/' + filename))
        put(binary, filename)
    for name in ('menu.dat', 'hdmenu.dat', 'fdmenu.dat', 'term.dat', 'national.msg', 'index.dsp'):
        put(ROOT / 'base' / name, name)
    for name in ('help.edx', 'lsn.edx'):
        put(ROOT / 'commands/dredix' / name, name)
    put(ROOT / 'commands/helphlp/help.hlp', 'help.hlp')
    put(ROOT / 'base/rmdir.cmd', 'sample.cmd')
    for name, data in [('keep.txt', b'line one\r\nline two\r\n\x1a'), ('gone.txt', b'g\r\n'),
                       ('test.bat', b'USER\r\nDIR B:KEEP.TXT\r\n\x1a')]:
        (folder / name).write_bytes(data)
        put(folder / name, name)

    commands = ['c f000000']

    def key(k):
        commands.extend(['key ' + KEYS.get(k, k), 'c 200000'])

    for index, (cmd, reply) in enumerate(CASES[group]):
        if cmd:
            if group == 'cli':
                for k in ['c', 'l', 's', 'Return']:
                    key(k)
            for k in cmd:
                key(k)
            key('Return')
        commands.append('c 4000000')
        for k in reply:
            key(k)
        commands.extend(['c 3000000', f'save "s{index}.bin" bin b800:0000 fa0'])
    commands.append('q')
    with (folder / 'log').open('wb') as log:
        subprocess.run(['pce-ibmpc', '-c', 'cfg', '-t', 'null', '-g', 'vga'], cwd=folder,
                       input=('\n'.join(commands)+'\n').encode(), stdout=log,
                       stderr=log, timeout=450, check=True)
    assert 'unknown key:' not in (folder/'log').read_text(errors='replace')
    screens = []
    for index in range(len(CASES[group])):
        frame = (folder / f's{index}.bin').read_bytes()
        screen = '\n'.join(frame[j:j+160:2].decode('cp437').rstrip() for j in range(0,3840,160)).strip()
        (folder / f's{index}.txt').write_text(screen)
        screens.append(screen)
    if group == 'cli':
        for name in ('sample.cmd', 'keep.txt', 'out.txt', 'joined.txt'):
            run('mcopy', '-i', 'fat.img', '::'+name, 'result-'+name)
        files = run('mdir', '-b', '-i', 'fat.img', '::*').stdout.lower()
        assert b'gone.txt' not in files
        keep = (folder/'result-keep.txt').read_bytes().split(b'\x1a')[0]
        assert (folder/'result-out.txt').read_bytes().split(b'\x1a')[0] == keep
        assert (folder/'result-joined.txt').read_bytes().split(b'\x1a')[0] == keep * 2
        assert 'Duplicate field' in screens[3] and 'SHARED=ON' in screens[4]
        assert 'PATH=B:\\ALPHA;B:\\BETA' in screens[18] and 'PATH=' in screens[20]
    return screens


def compare(work, group):
    with ThreadPoolExecutor(2) as pool:
        old, new = pool.map(lambda v: session(work, group, v), ['original', 'rebuilt'])
    for index, (a,b) in enumerate(zip(old,new)):
        if group == 'batch' and index == 1:
            # The maintained USER message and trailing blank-line echoes differ.
            # Free-space counts depend on the size of BATCH itself.
            for screen in (a,b):
                assert 'User Number = 0' in screen and 'KEEP     TXT' in screen
                assert screen.count('Directory of Drive B') == 1 and screen.endswith('B>')
            assert 'Note:' in a and 'Note:' not in b
        elif group == 'cli' and index in (23, 24):
            assert 'CONCURRENT PIP VERSION 4.1N' in b
            assert a == b.replace('CONCURRENT PIP VERSION 4.1N', 'CONCURRENT PIP VERSION 4.1')
        else:
            assert a == b, (group,index,a,b)
    if group == 'cli':
        for name in ('sample.cmd','keep.txt','out.txt','joined.txt'):
            result = 'result-'+name
            assert (work/'cli-original'/result).read_bytes() == (work/'cli-rebuilt'/result).read_bytes()
    print(f'PASS: {group}, {len(old)} paired screens', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('groups', nargs='*')
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix='cdos-release-'))
    try:
        for group in args.groups or CASES:
            compare(work, group)
    except BaseException:
        print('Diagnostics retained in', work, flush=True)
        raise
    shutil.rmtree(work)
