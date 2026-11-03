#!/usr/bin/env python3
"""Verify real allocation info/FAT descriptor and invalid 1Ch/36h drive codes."""
from pathlib import Path
import re,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parent.parent


def check():
    folder=Path(tempfile.mkdtemp(prefix='cdos-allocation-'))
    print('Diagnostics:',folder,flush=True)
    def run(*args):return subprocess.run(args,cwd=folder,capture_output=True,check=True)
    shutil.copyfile(ROOT/'media/cdos86.img',folder/'cdos86.img')
    run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
    boot=(folder/'fat.img').read_bytes()[:512]
    word=lambda at:int.from_bytes(boot[at:at+2],'little')
    bps=word(11);spc=boot[13]
    units=(word(19)-word(14)-boot[16]*word(22)-(word(17)*32+bps-1)//bps)//spc
    run('nasm','-f','bin',str(ROOT/'kernel/rsp3/tests/dos_alloc.asm'),
        '-DBPS='+str(bps),'-DSPC='+str(spc),'-DUNITS='+str(units),'-DMEDIA='+str(boot[21]),'-o','alloc.com')
    run('mcopy','-i','fat.img','alloc.com','::')
    cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"')
    cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/'media'/m[1]).resolve())+'"',cfg)
    cfg=cfg.replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','fat.img')
    (folder/'cdos86.cfg').write_text(cfg)
    commands=['c f000000']
    for char in 'b:alloc\n':
        key={':':'+Shift Semicolon -Shift','\n':'Return'}.get(char,char)
        commands+=['key '+key,'c 200000']
    commands+=['c 8000000','save "result.bin" bin b800:0000 fa0','q']
    with (folder/'pce.log').open('wb') as log:
        subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=folder,
                       input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,timeout=60,check=True)
    v=(folder/'result.bin').read_bytes()
    screen='\n'.join(''.join(chr(x) if 32<=x<127 else ' ' for x in v[i:i+160:2]) for i in range(0,3840,160))
    assert 'DOS ALLOCATION PASS' in screen and 'FAIL' not in screen,screen
    assert [l.strip() for l in screen.splitlines() if l.strip()][-1]=='A>',screen
    print('PASS: live 1Bh/1Ch/36h on CP/M and FAT, BPB geometry, actual FAT media byte, unchanged FAT pointer, all invalid-drive samples and current-drive preservation')


if __name__=='__main__':check()
