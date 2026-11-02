#!/usr/bin/env python3
"""Check nested DOS EXEC, shared handles and Ctrl-C return on scratch media."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(os.environ.get('CDOS_TEST_ROOT',Path(__file__).resolve().parent.parent))


def check(abort=False):
    with tempfile.TemporaryDirectory(prefix='cdos-handles-') as temporary:
        folder=Path(temporary)
        def run(*args):
            return subprocess.run(args,cwd=folder,check=True,capture_output=True)
        shutil.copyfile(ROOT/'media/cdos86.img',folder/'cdos86.img')
        run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
        for name,source in [('stamp','dos_handle_parent.asm'),('child','dos_handle_child.asm'),('grand','dos_handle_grand.asm')]:
            args=['nasm','-f','bin',str(ROOT/'kernel/rsp3/tests'/source),'-o',name+'.com']
            if abort:args+=['-DABORT']
            run(*args);run('mcopy','-i','fat.img',name+'.com','::')
        cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"')
        cfg=cfg.replace('driver      = "sdl:lowpass=5000"','driver      = "null"')
        cfg=cfg.replace('file     = "cdostools.img"','file     = "fat.img"')
        (folder/'cdos86.cfg').write_text(cfg)
        commands=['c f000000']
        for char in 'b:stamp\n':
            key={':':'+Shift Semicolon -Shift','\n':'Return'}.get(char,char)
            commands+=['key '+key,'c 200000']
        commands+=['c 8000000','save "result.bin" bin b800:0000 fa0','q']
        with (folder/'pce.log').open('wb') as log:
            subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=folder,
                           input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,
                           timeout=60,check=True)
        video=(folder/'result.bin').read_bytes()
        screen='\n'.join(''.join(chr(v) if 32<=v<127 else ' ' for v in video[i:i+160:2]) for i in range(0,3840,160))
        assert 'HANDLE EXEC PASS' in screen and 'FAIL' not in screen,screen
        assert [l.strip() for l in screen.splitlines() if l.strip()][-1]=='A>',screen
        for name,expected in [('redir.dat',b'PCGP'),('leak.dat',b'Q'),('grand.dat',b'R')]:
            run('mcopy','-i','fat.img','::'+name,name)
            assert (folder/name).read_bytes()==expected,(name,(folder/name).read_bytes())
    print('PASS: live nested EXEC '+('Ctrl-C' if abort else 'normal')+' return; shared handles, exact EOF and child-only file cleanup')


if __name__=='__main__':
    check()
    check(abort=True)
