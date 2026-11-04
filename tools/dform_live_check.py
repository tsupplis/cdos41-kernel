#!/usr/bin/env python3
"""Format a disposable FAT12 360K floppy with the actual CDOS DFORM/XIOS.

Checks physical geometry, complete FAT/root metadata, data fill, an independent
mtools write/read, empty-media recovery and a rebuilt kernel cold boot.
Only newly created images are modified. Failed tests retain their diagnostics.
"""
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--format',type=int,choices=(360,720,1200,1440),default=360)
capacity=parser.parse_args().format
cylinders,spt,spc,media,spf,roots={360:(40,9,2,0xfd,2,112),720:(80,9,2,0xf9,3,112),1200:(80,15,1,0xf9,7,224),1440:(80,18,1,0xf0,9,224)}[capacity]
total=cylinders*2*spt
metadata=1+2*spf+roots//16
ROOT = Path(__file__).resolve().parent.parent
folder = Path(tempfile.mkdtemp(prefix='dform-live-'))
print('Diagnostics:', folder, flush=True)

def run(*args):
    return subprocess.run(args, cwd=folder, check=True, capture_output=True)

shutil.copyfile(ROOT/'media/diskdefs', folder/'diskdefs')
run('python3', str(ROOT/'tools/cpm86twist.py'), 'untwist',
    str(ROOT/'media/cdos86base.img'), 'logical.img')
run('cpmcp', '-f', 'ccpm86-320', 'logical.img',
    str(ROOT/'kernel/sysgen/ccpm.sys'), '0:CCPM.SYS')
run('cpmcp', '-f', 'ccpm86-320', 'logical.img',
    str(ROOT/'commands/dform/dform.cmd'), '0:DFORM.CMD')
if capacity==1440:
    shutil.copyfile(ROOT/'tools/floppy_probe.a86',folder/'fatprobe.a86')
    run('cpm86_asm86','fatprobe')
    run('cpm86_gencmd','fatprobe.h86','8080')
    run('cpmcp','-f','ccpm86-320','logical.img','fatprobe.cmd','0:FATPROBE.CMD')
run('python3', str(ROOT/'tools/cpm86twist.py'), 'twist', 'logical.img', 'source.img')
# Start with eight physical sectors and nonzero old data. Formatting must
# replace the geometry and clear every directory/FAT byte, not merely the IDs.
run('psi', '-n', str(capacity), '-F', '165', '-o', 'target.psi')
cfg = (ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"', 'driver = "null"').replace('sdl:lowpass=5000', 'null')
cfg = cfg.replace('cdos86.img', 'source.img').replace('cdostools.img', 'target.psi')
cfg = re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',
             lambda m: 'path = "'+str((ROOT/'media'/m[1]).resolve())+'"', cfg)
(folder/'test.cfg').write_text(cfg)
commands = ['c f000000']
keys = {':': '+Shift Semicolon -Shift', ' ': 'Space', '[': 'LeftBracket', ']': 'RightBracket'}
for ch in f'dform b: [dos{capacity}] [v]':
    commands += ['key '+keys.get(ch, ch), 'c 200000']
commands += ['key Return', 'c 6000000', 'key y', 'c 40000000', 'c 40000000',
             'save "format.bin" bin b800:0000 fa0', 'q']

def pce(commands, name):
    with (folder/(name+'.log')).open('wb') as log:
        subprocess.run(['pce-ibmpc', '-c', 'test.cfg', '-t', 'null', '-g', 'vga'],
                       cwd=folder, input=('\n'.join(commands)+'\n').encode(),
                       stdout=log, stderr=log, check=True, timeout=240)

def screen(name):
    b = (folder/(name+'.bin')).read_bytes()
    text = '\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
    (folder/(name+'.txt')).write_text(text)
    return text

pce(commands, 'format')
assert 'Format complete.' in screen('format')
info = run('psi', 'target.psi', '-f').stdout.decode()
assert 'BAD-ID' not in info and f'{total} + 0' in info, info
run('psi', 'target.psi', '-O', 'raw', '-o', 'target.img')
b = (folder/'target.img').read_bytes()
assert len(b) == total*512
boot=bytearray((ROOT/'commands/dform/fatboot.bin').read_bytes())
struct.pack_into('<HBHBHHBHHHH',boot,11,512,spc,1,2,roots,total,media,spf,spt,2,0)
assert b[:512] == boot
fat=bytes([media,255,255])+bytes(spf*512-3)
assert b[512:(1+spf)*512] == b[(1+spf)*512:(1+2*spf)*512] == fat
assert not any(b[(1+2*spf)*512:metadata*512]), 'Root directory is not empty'
assert b[metadata*512:] == bytes([0xf6])*((total-metadata)*512), 'Unexpected formatted data fill'
run('mdir', '-i', 'target.img', '::')
probe = b'DFORM FAT12 interoperability check\r\n'
(folder/'probe.txt').write_bytes(probe)
run('mcopy', '-i', 'target.img', 'probe.txt', '::PROBE.TXT')
assert run('mtype', '-i', 'target.img', '::PROBE.TXT').stdout == probe
if capacity==1440:
    # Exercise native BDOS allocation and record I/O past FAT sector seven.
    probe_commands=['c f000000']
    for ch in 'fatprobe':
        probe_commands+=['key '+ch,'c 200000']
    probe_commands+=['key Return','c 40000000','c 40000000',
                     'save "native.bin" bin b800:0000 fa0','q']
    pce(probe_commands,'native')
    assert 'Native FAT write/read passed.' in screen('native')
# Preserve the original empty format: the mtools probe must not occupy the
# first root entry/cluster required by the historical system bootstrap.
(folder/'formatted.img').write_bytes(b)
from dskmaint_live_check import cold_boot
cold_boot(folder, folder/'formatted.img', 'empty', '', None,
          ['Insert boot disk'])
cold_boot(folder, folder/'formatted.img', 'rebuilt', 'CCPM.SYS',
          ROOT/'kernel/sysgen/ccpm.sys', ['Concurrent', 'A>'])
print(f'PASS: CDOS {capacity}K format/verify, FAT12, mtools I/O, empty recovery and rebuilt kernel cold boot')
shutil.rmtree(folder)
