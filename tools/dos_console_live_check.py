#!/usr/bin/env python3
"""Exercise CON raw/cooked mode, version and inherited aliases through real keys."""
from pathlib import Path
import os,shutil,subprocess,tempfile
ROOT=Path(os.environ.get('CDOS_TEST_ROOT',Path(__file__).resolve().parent.parent))


def check():
    with tempfile.TemporaryDirectory(prefix='cdos-rawcon-') as temporary:
        folder=Path(temporary)
        def run(*args):return subprocess.run(args,cwd=folder,capture_output=True,check=True)
        shutil.copyfile(ROOT/'media/cdos86.img',folder/'cdos86.img')
        run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
        for name,source,defines in [('rawcon','dos_rawcon.asm',[]),('rawchild','dos_rawchild.asm',[]),('probe','dos_rawcon.asm',['-DPROBE'])]:
            run('nasm','-f','bin',str(ROOT/'kernel/rsp3/tests'/source),*defines,'-o',name+'.com')
            run('mcopy','-i','fat.img',name+'.com','::')
        cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"')
        cfg=cfg.replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','fat.img')
        (folder/'cdos86.cfg').write_text(cfg)
        commands=['c f000000']
        def type_command(text):
            for char in text+'\n':
                key={':':'+Shift Semicolon -Shift','\n':'Return','.':'Period'}.get(char,char)
                commands.extend(['key '+key,'c 200000'])
            commands.append('c 4000000')
        def save(label):commands.append(f'save "{label}.bin" bin b800:0000 fa0')
        type_command('b:rawcon')
        save('raw-ready')
        commands+=['key j','c 400000']
        save('raw-noecho')
        commands+=['key Backspace','c 200000','key +Ctrl z -Ctrl','c 200000',
                   'key +Ctrl c -Ctrl','c 200000','key Return','c 1000000']
        save('extended')
        commands+=['key Up','c 2000000']
        save('cooked-ready')
        for key in ['a','b','Backspace','+Shift c -Shift','Return']:
            commands+=['key '+key,'c 200000']
        commands+=['c 4000000']
        save('result')
        type_command('b:probe')
        save('probe')
        commands+=['q']
        with (folder/'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=folder,
                           input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,
                           timeout=60,check=True)
        def video(label):return (folder/(label+'.bin')).read_bytes()
        def text(label):
            v=video(label)
            return '\n'.join(''.join(chr(c) if 32<=c<127 else ' ' for c in v[i:i+160:2]) for i in range(0,3840,160))
        for label,marker in [('raw-ready','RAW INPUT READY'),('raw-noecho','RAW INPUT READY'),
                             ('extended','EXTENDED READY'),('cooked-ready','COOKED READY'),
                             ('result','RAWCON PASS'),('probe','MODE RESET PASS')]:
            assert marker in text(label) and 'FAIL' not in text(label),(label,text(label))
        assert video('raw-ready')[:3840]==video('raw-noecho')[:3840],text('raw-noecho')
        assert b'RAWBYTES:\xfd\xfe\xff:END' in video('cooked-ready')[0::2],text('cooked-ready')
        for label in ['result','probe']:
            assert [l.strip() for l in text(label).splitlines() if l.strip()][-1]=='A>',text(label)
    print('PASS: live version/OEM/serial; raw Ctrl-C/Z/Backspace/CR and extended key, no echo, FD-FF output, cooked editing, DUP/EXEC sharing and next-program reset',flush=True)


if __name__=='__main__':check()
