"""Format a disposable FAT floppy with DSKMAINT and cold-boot its written sector."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import argparse
import re
import struct

ROOT = Path(__file__).resolve().parents[1]


def run(folder, *args, **kwargs):
    return subprocess.run(args, cwd=folder, check=True, capture_output=True, **kwargs)


def session(folder, drive_a, drive_b, commands):
    config = (ROOT / 'media/cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"')
    config = config.replace('sdl:lowpass=5000', 'null')
    config = config.replace('cdos86.img', drive_a).replace('cdostools.img', drive_b)
    config = re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',
                    lambda m: 'path = "'+str((ROOT/'media'/m[1]).resolve())+'"', config)
    (folder/'cfg').write_text(config)
    with (folder/'pce.log').open('wb') as log:
        subprocess.run(['pce-ibmpc','-c','cfg','-t','null','-g','vga'],cwd=folder,
                       input=('\n'.join(commands+['q'])+'\n').encode(),
                       stdout=log,stderr=log,timeout=150,check=True)


def screen(folder, label):
    data = (folder/(label+'.bin')).read_bytes()
    text = '\n'.join(data[i:i+160:2].decode('cp437').rstrip() for i in range(0,3840,160))
    (folder/(label+'.txt')).write_text(text)
    return text


def format_floppy(folder, capacity=360):
    shutil.copyfile(ROOT/'media/diskdefs',folder/'diskdefs')
    run(folder,'python3',str(ROOT/'tools/cpm86twist.py'),'untwist',str(ROOT/'media/cdos86base.img'),'logical.img')
    for src in ('kernel/sysgen/ccpm.sys','commands/dskmaint/dskmaint.cmd'):
        run(folder,'cpmcp','-f','ccpm86-320','logical.img',str(ROOT/src),'0:')
    run(folder,'python3',str(ROOT/'tools/cpm86twist.py'),'twist','logical.img','maint.img')
    floppy = folder/'formatted.img'
    floppy.write_bytes(bytes(capacity*1024))
    commands = ['c f000000']
    for ch in list('dskmaint')+['Space','f','Return']:
        commands.extend(['key '+ch,'c 200000'])
    for label, key in [('type',{360:'F5',720:'F6',1200:'F7',1440:'F8'}[capacity]),('drive','F4'),('confirm','y')]:
        commands.extend(['c 4000000', f'save "{label}.bin" bin b800:0000 fa0','key '+key])
    commands.extend(['c 40000000','save "formatted.bin" bin b800:0000 fa0'])
    session(folder,'maint.img','formatted.img',commands)
    for label in ('type','drive','confirm','formatted'):
        screen(folder,label)
    spt,spc,media,spf,roots={360:(9,2,0xfd,2,112),720:(9,2,0xf9,3,112),1200:(15,1,0xf9,7,224),1440:(18,1,0xf0,9,224)}[capacity]
    sector=bytearray((ROOT/('commands/dskmaint/dosboot.bin' if capacity==360 else 'commands/dskmaint/dosbootx.bin')).read_bytes())
    struct.pack_into('<HBHBHHBHHHH',sector,11,512,spc,1,2,roots,capacity*2,media,spf,spt,2,0)
    assert floppy.read_bytes()[:512] == sector, 'DSKMAINT did not write the release sector to drive B'
    run(folder,'mdir','-i','formatted.img','::')
    return floppy


def build_low_kernel(folder):
    # This release bootstrap enters at 0060:0000. Generate a matching system
    # in isolation; the normal CP/M boot image uses OSSTART=6000h.
    gen = folder/'sysgen'
    gen.mkdir()
    source=ROOT/'kernel/sysgen'
    # Stage only declared RSPs. The selected response file owns inclusion,
    # just as in the normal SYSGEN build; stale RSPs are never enumerated.
    from sysgen_check import resident_names
    names=resident_names((source/'ccpm.sys').read_bytes())
    selected={'pin.rsp','clock.rsp','pctmp.rsp','confid.rsp'}
    for pattern in ('*.con','*.rsp'):
        for component in source.glob(pattern):
            if component.suffix=='.rsp' and component.name not in selected:
                continue
            shutil.copyfile(component,gen/component.name)
    response='genfidd.in' if 'CONFIDD' in names else 'genccpm.in'
    recipe=(source/response).read_text()
    assert recipe.count('osstart=6000') == 1
    run(gen,'emu2',str(ROOT/'commands/genccpm/genccpm.cmd'),
        input=recipe.replace('osstart=6000','osstart=60').encode(),timeout=30)
    kernel=gen/'ccpm.sys'
    assert int.from_bytes(kernel.read_bytes()[3:5],'little')==0x60
    return kernel


def cold_boot(folder, floppy, case, name, system, expected):
    target=folder/(case+'.img')
    shutil.copyfile(floppy,target)
    if system:
        run(folder,'mcopy','-i',target.name,str(system),'::'+name)
    session(folder,target.name,'absent.img',['c f000000',f'save "{case}.bin" bin b800:0000 fa0'])
    output=screen(folder,case)
    for phrase in expected:
        assert phrase in output,(case,phrase,output)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--format',type=int,choices=(360,720,1200,1440),default=360)
    capacity=parser.parse_args().format
    work=Path(tempfile.mkdtemp(prefix='cdos-dskmaint-'))
    print('DSKMAINT diagnostics:',work,flush=True)
    floppy=format_floppy(work,capacity)
    print(f'PASS: DSKMAINT formatted DOS {capacity}K with the checked system bootstrap',flush=True)
    cold_boot(work,floppy,'empty','',None,['Not a boot disk','Insert boot disk'])
    system=build_low_kernel(work)
    cold_boot(work,floppy,'ccpm','CCPM.SYS',system,['Concurrent','A>'])
    cold_boot(work,floppy,'cpm3','CPM3.SYS',system,['Concurrent','A>'])
    print('PASS: empty-disk recovery, both system filenames using the low-linked rebuilt kernel')
    shutil.rmtree(work)
