#!/usr/bin/env python3
"""DOS switch-character ABI, native delimiter separation and EXEC persistence."""
from pathlib import Path
import re,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parent.parent


def check():
    with tempfile.TemporaryDirectory(prefix='cdos-switch-') as temporary:
        folder=Path(temporary)
        def run(*args):return subprocess.run(args,cwd=folder,capture_output=True,check=True)
        shutil.copyfile(ROOT/'media/cdos86.img',folder/'cdos86.img')
        run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
        for name,defs in [('switch',[]),('swchild',['-DCHILD']),('swprobe',['-DPROBE'])]:
            run('nasm','-f','bin',str(ROOT/'kernel/rsp3/tests/dos_switch.asm'),*defs,'-o',name+'.com')
            run('mcopy','-i','fat.img',name+'.com','::')
        cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"')
        cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/'media'/m[1]).resolve())+'"',cfg)
        cfg=cfg.replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','fat.img')
        (folder/'cdos86.cfg').write_text(cfg)
        commands=['c f000000']
        for text,label in [('b:switch','parent'),('b:swprobe','probe')]:
            for char in text+'\n':
                key={':':'+Shift Semicolon -Shift','\n':'Return','.':'Period'}.get(char,char)
                commands+=['key '+key,'c 200000']
            commands+=['c 8000000',f'save "{label}.bin" bin b800:0000 fa0']
        commands+=['q']
        with (folder/'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=folder,
                           input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,timeout=60,check=True)
        for label,expected in [('parent','DOS SWITCH EXEC PASS'),('probe','DOS SWITCH PERSIST PASS')]:
            video=(folder/(label+'.bin')).read_bytes()
            screen='\n'.join(''.join(chr(v) if 32<=v<127 else ' ' for v in video[i:i+160:2]) for i in range(0,3840,160))
            assert expected in screen and 'FAIL' not in screen,screen
            assert [l.strip() for l in screen.splitlines() if l.strip()][-1]=='A>',screen
    print('PASS: live DOS 37h defaults, get/set ABI, rejected selectors, unchanged native BDOS delimiter, nested EXEC sharing and next-launch persistence')


if __name__=='__main__':check()
