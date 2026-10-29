#!/usr/bin/env python3
"""Boot disposable 4.1 media and exercise shell, editor and console switching."""
from pathlib import Path
import argparse
import re
import shutil
import subprocess
import tempfile

from editor_cases import check_recall, check_editor

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / 'media'


def screen(path):
    data = path.read_bytes()
    assert len(data) == 4000, 'Missing text video memory'
    return '\n'.join(''.join(chr(c) if 32 <= c < 127 else ' '
                             for c in data[at:at + 160:2])
                     for at in range(0, 4000, 160))


def check(video):
    emulator = shutil.which('pce-ibmpc')
    assert emulator, 'pce-ibmpc is required for check-pce'
    with tempfile.TemporaryDirectory(prefix='cdos-boot-') as td:
        folder = Path(td)
        for name in ['cdos86.img', 'cdostools.img']:
            shutil.copyfile(MEDIA / name, folder / name)
        # Retain the launcher's CPU, ROMs and disk/controller configuration.
        # Only the host terminal/speaker drivers become null for this test.
        cfg = (MEDIA / 'cdos86.cfg').read_text()
        cfg = cfg.replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        (folder / 'cdos86.cfg').write_text(cfg)
        commands = ['c f000000']
        snapshots = []
        editing = []
        switches = []
        symbols = dict((name, int(value, 16)) for value, name in
                       re.findall(r"\b([0-9A-F]{4})\s+([A-Z][A-Z0-9]*)",
                                  (ROOT / "kernel/con/squid.sym").read_text()))
        system = (ROOT / "kernel/sysgen/ccpm.sys").read_bytes()
        data_base = int.from_bytes(system[12:14], "little")
        top_address = f'{data_base:04x}:{symbols["TOPSCREEN"]:04x}'

        def save(name):
            snapshots.append((name, folder / (name + '.bin')))
            commands.append(f'save "{name}.bin" bin b800:0000 fa0')

        def type_command(text):
            keys = {' ': 'Space', '\n': 'Return', '\t': 'Tab', ';': 'Semicolon', '.': 'Period', '=': 'Equal', '[': 'LeftBracket', ']': 'RightBracket'}
            for char in text:
                if char == ':':
                    commands.extend(['key +Shift Semicolon -Shift', 'c 200000'])
                else:
                    commands.extend(['key ' + keys.get(char, char), 'c 200000'])
            commands.append('c 2000000')

        def key(chord):
            names = {'ctrl': 'Ctrl', 'alt': 'Alt', 'backspace': 'Backspace',
                     'left': 'Left', 'right': 'Right', 'up': 'Up',
                     'home': 'Home', 'end': 'End', 'delete': 'Delete', 'tab': 'Tab'}
            parts = chord.split('-')
            modifiers = [names[p] for p in parts[:-1]]
            sequence = ['+' + p for p in modifiers]
            sequence.append(names.get(parts[-1], parts[-1]))
            sequence.extend('-' + p for p in reversed(modifiers))
            commands.extend(['key ' + ' '.join(sequence), 'c 200000'])

        def current(expected):
            name = 'editor-' + str(len(editing))
            save(name)
            editing.append((name, expected))

        def shortcut(chord, console):
            key(chord)
            commands.append('c 2000000')
            name = 'switch-' + str(len(switches)) + '.bin'
            commands.append(f'save "{name}" bin {top_address} 1')
            switches.append((name, console))

        save('boot')
        check_recall(type_command, key, current, shortcut)
        check_editor(type_command, key, current, shortcut)
        for console in range(4):
            shortcut('ctrl-alt-' + str(console + 1), console)
        for console in [0, 1, 2, 3, 0]:
            shortcut('ctrl-alt-tab', console)
        type_command('dir\n')
        save('dir')
        type_command('pip\n')
        save('pip')
        type_command('\n')
        save('return')
        type_command('pip b:bootchk.txt=a:startup.0\n')
        save('copy')
        type_command('dir b:\n')
        save('drive-b')
        type_command('user 1\n')
        save('user')
        type_command('user 0\n')
        type_command('cls\n')
        save('cls')
        type_command('sysdisk\n')
        save('sysdisk')
        type_command('sysdisk [off]\n')
        save('sysdisk-off')
        type_command('sysdisk [on]\n')
        save('sysdisk-on')
        commands.append('q')
        with (folder / 'pce.log').open('wb') as log:
            result = subprocess.run([emulator, '-c', 'cdos86.cfg', '-t', 'null', '-g', video],
                                    cwd=folder, input=('\n'.join(commands) + '\n').encode(),
                                    stdout=log, stderr=subprocess.STDOUT, timeout=120)
        assert result.returncode == 0, (folder / 'pce.log').read_text(errors='replace')[-5000:]
        text = {name: screen(path) for name, path in snapshots}
        for name, expected in editing:
            lines = [line.rstrip() for line in text[name].splitlines()[:24] if line.strip()]
            actual = ''.join(lines)
            wanted = ('A>' + expected).expandtabs(8)
            assert (actual.endswith(wanted) or bool(expected) and lines[-1].lstrip() == expected.expandtabs(8)), (name, expected, text[name])
        for name, expected in switches:
            actual = (folder / name).read_bytes()
            assert actual == bytes([expected]), (name, expected, actual)
        prompt = lambda s: bool(re.search(r'^A>\s*$', s, re.M))
        assert 'Concurrent DOS 4.1' in text['boot'] and prompt(text['boot']), text['boot']
        assert 'PIP' in text['dir'].upper() and 'STARTUP' in text['dir'].upper() and prompt(text['dir']), text['dir']
        assert re.search(r'^\*\s*$', text['pip'], re.M), text['pip']
        assert prompt(text['return']), text['return']
        assert prompt(text['copy']) and 'error' not in text['copy'].lower(), text['copy']
        assert 'BOOTCHK' in text['drive-b'].upper() and prompt(text['drive-b']), text['drive-b']
        assert 'User Number = 1' in text['user'] and 'Note:' not in text['user'], text['user']
        assert prompt(text['cls']) and 'Concurrent' not in text['cls'], text['cls']
        assert "Can't Find Command" not in text['sysdisk'] and prompt(text['sysdisk']), text['sysdisk']
        assert 'The system drive is off' in text['sysdisk-off'], text['sysdisk-off']
        assert prompt(text['sysdisk-on']) and 'system drive is off' not in text['sysdisk-on'].split('sysdisk [on]')[-1], text['sysdisk-on']
        subprocess.run(['python3', str(ROOT / 'tools/cpm86twist.py'), 'untwist',
                        str(folder / 'cdostools.img'), str(folder / 'logical.img')], check=True)
        subprocess.run(['cpmcp', '-f', 'ccpm86-320', str(folder / 'logical.img'),
                        '0:bootchk.txt', str(folder / 'bootchk.txt')], cwd=MEDIA, check=True)
        content = (folder / 'bootchk.txt').read_bytes().rstrip(b'\x00\x1a')
        assert content == (MEDIA / 'startup.0').read_bytes(), 'PIP changed the copied text'
        print(f'PASS: PCE {video}: 4.1 prompt, DIR, native PIP, cross-drive copy, line editing/recall, console shortcuts, CLS, USER and SYSDISK')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', default='vga', choices=['vga', 'cga'])
    check(parser.parse_args().video)
