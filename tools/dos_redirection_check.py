#!/usr/bin/env python3
"""Check GET/PUT/RDR with DOS children on disposable CP/M and FAT PCE disks."""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(os.environ.get('CDOS_TEST_ROOT', Path(__file__).resolve().parent.parent))
FIXTURES = ROOT / 'kernel/rsp3/tests'
PAYLOAD = b'REDIR PAYLOAD\r\n\0\x1a\xff'
BINARY = bytes(range(256))*2 + b'LAST'


def check(group):
    with tempfile.TemporaryDirectory(prefix='cdos-dos-redir-') as temporary:
        folder = Path(temporary)

        def run(*args):
            result = subprocess.run(args, cwd=folder, capture_output=True)
            assert result.returncode == 0, (args, result.stderr.decode(errors='replace'))
            return result

        shutil.copyfile(ROOT/'media/cdos86.img', folder/'cdos86.img')
        shutil.copyfile(ROOT/'media/diskdefs', folder/'diskdefs')
        twist = str(ROOT/'tools/cpm86twist.py')
        run('python3', twist, 'untwist', 'cdos86.img', 'boot.logical')
        # Remove two irrelevant commands from this disposable boot copy only.
        run('cpmrm', '-f', 'ccpm86-320', 'boot.logical', '0:show.cmd', '0:set.cmd')
        for name in ['put', 'get', 'rdr']:
            run('cpmcp', '-f', 'ccpm86-320', 'boot.logical',
                str(ROOT/f'commands/putget/{name}.cmd'), '0:'+name+'.cmd')
        run('python3', twist, 'twist', 'boot.logical', 'cdos86.img')
        run('mformat', '-C', '-i', 'fat.img', '-t', '40', '-h', '2', '-n', '8', '-c', '2', '::')
        for name, source in [('child','dos_stream.asm'), ('copy','dos_copy.asm'), ('emit','dos_emit.asm')]:
            run('nasm', '-f', 'bin', str(FIXTURES/source), '-o', name+'.com')
            run('mcopy', '-i', 'fat.img', name+'.com', '::')
        run('nasm', '-f', 'bin', '-DEXE', str(FIXTURES/'dos_emit.asm'), '-o', 'exe.bin')
        image = (folder/'exe.bin').read_bytes()
        size = len(image)+512
        header = struct.pack('<14H', 0x5a4d, size%512, (size+511)//512, 0, 32,
                             0x100, 0xffff, 0, len(image)-2, 0, 0, 0, 0x1c, 0) + b'\0'*(512-28)
        (folder/'emit.exe').write_bytes(header+image)
        run('mcopy', '-i', 'fat.img', 'emit.exe', '::')
        for name, content in [('stream.in', b'\0\x1aZONE\r\nTWO\r\n'),
                              ('binary.in', BINARY), ('echo.in', b'ECHO INPUT\r\n')]:
            (folder/name).write_bytes(content)
            run('mcopy', '-i', 'fat.img', name, '::')
        cfg = (ROOT/'media/cdos86.cfg').read_text()
        cfg = cfg.replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        cfg = cfg.replace('file     = "cdostools.img"', 'file     = "fat.img"')
        (folder/'cdos86.cfg').write_text(cfg)
        groups = {
            'streams': [('stream', 'rdr [b:stream.in,b:stream.out] b:child.com'),
                        ('binary', 'rdr [b:binary.in,b:binary.out] b:copy'),
                        ('get', 'get [b:stream.in] b:child.com')],
            'output': [('put', 'put [b:emit.out] b:emit.com'),
                       ('append', 'put [b:emit.out,a,eo] b:emit.exe'),
                       ('cpm', 'put [a:cpm.out] b:emit.com')],
            'errors': [('missing', 'rdr [b:missing.in,b:bad.out] b:copy.com'),
                       ('same', 'rdr [b:echo.in,b:echo.in] b:copy.com'),
                       ('recover', 'rdr [b:echo.in,b:echo.out,ei] b:copy.com')],
        }
        commands = ['c f000000']
        for label, command in groups[group]:
            for char in command+'\n':
                key = {':':'+Shift Semicolon -Shift', '\n':'Return', ' ':'Space',
                       '.':'Period', '[':'LeftBracket', ']':'RightBracket', ',':'Comma'}.get(char,char)
                commands += ['key '+key, 'c 200000']
            commands += ['c 10000000', f'save "{label}.bin" bin b800:0000 fa0']
        commands.append('q')
        with (folder/'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc', '-c', 'cdos86.cfg', '-t', 'null', '-g', 'vga'],
                           cwd=folder, input=('\n'.join(commands)+'\n').encode(),
                           stdout=log, stderr=log, timeout=60, check=True)
        screens = {}
        for label, _ in groups[group]:
            video = (folder/(label+'.bin')).read_bytes()
            text = '\n'.join(''.join(chr(v) if 32<=v<127 else ' '
                                      for v in video[i:i+160:2]) for i in range(0,3840,160))
            screens[label] = text
            assert [l.strip() for l in text.splitlines() if l.strip()][-1] == 'A>', (label,text)
            assert 'Interrupt from' not in text and 'FAIL' not in text, (label,text)
            if group != 'errors':
                assert 'failed' not in text.lower() and 'cannot open or bind' not in text, (label,text)
        expected = {'streams':[('stream.out',b'ONE\rTWO\rTEXT!\0\0\x1a\xff'),('binary.out',BINARY)],
                    'output':[('emit.out',PAYLOAD*2)], 'errors':[('echo.out',b'ECHO INPUT\r\n'),('echo.in',b'ECHO INPUT\r\n')]}
        for name, data in expected[group]:
            run('mcopy', '-i', 'fat.img', '::'+name, name)
            assert (folder/name).read_bytes() == data, (name,(folder/name).read_bytes()[:200])
        if group == 'output':
            assert 'STDERR CONSOLE' in screens['put'], screens['put']
            assert 'REDIR PAYLOAD' in screens['append'], screens['append']
            run('python3',twist,'untwist','cdos86.img','result.logical')
            run('cpmcp','-f','ccpm86-320','result.logical','0:cpm.out','cpm.out')
            data=(folder/'cpm.out').read_bytes()
            assert data[:len(PAYLOAD)]==PAYLOAD and all(v in (0,26) for v in data[len(PAYLOAD):])
        if group == 'errors':
            assert 'cannot open or bind stream' in screens['missing'], screens['missing']
            assert 'CLI command execution failed' in screens['same'], screens['same']
            assert 'ECHO INPUT' in screens['recover'], screens['recover']
            assert run('mdir','-i','fat.img','::').stdout.find(b'BAD') == -1
    print('PASS: DOS redirection '+group+'; exact bytes, stderr and shell recovery; disposable disks')


if __name__ == '__main__':
    for group in ['streams','output','errors']:
        check(group)
