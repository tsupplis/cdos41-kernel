"""CDOS CP/M-media user view and system-drive FM.CFG fallback, in PCE."""
from pathlib import Path
import tempfile,subprocess,re,sys,shutil,argparse
parser=argparse.ArgumentParser()
parser.add_argument("--boot-image",type=Path)
parser.add_argument("--base-image",type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[3]
folder=Path(tempfile.mkdtemp(prefix='fm-users-'));print(folder,flush=True)
shutil.copyfile(root/'media/diskdefs',folder/'diskdefs')
def run(*args):
    subprocess.run(args,cwd=folder,check=True,capture_output=True)
def convert(mode,source,dest):
    run(sys.executable,str(root/'tools/cpm86twist.py'),mode,str(source),str(dest))
convert('untwist',args.boot_image or root/'media/cdos86.img',folder/'boot.logical')
config=folder/'fm.cfg';config.write_bytes(b'OBJECT FG COLOR=7\r\nOBJECT BG COLOR=1\r\n\x1a')
run('cpmcp','-f','ccpm86-320','boot.logical',str(config),'0:FM.CFG')
convert('twist',folder/'boot.logical',folder/'cdos86.img')
convert('untwist',args.base_image or root/'media/cdos86base.img',folder/'data.logical')
# libdsk cannot identify an entirely E5-filled image. Give the disposable
# empty filesystem the same reserved track as the boot fixture.
data=bytearray((folder/'data.logical').read_bytes())
data[:4096]=(folder/'boot.logical').read_bytes()[:4096]
(folder/'data.logical').write_bytes(data)
run('cpmcp','-f','ccpm86-320','data.logical',str(root/'commands/fm/fmview.cmd'),'4:FMVIEW.CMD')
for user in [0,4]:
    p=folder/('u%d.txt'%user);p.write_text('User fixture\r\n')
    run('cpmcp','-f','ccpm86-320','data.logical',str(p),str(user)+':')
convert('twist',folder/'data.logical',folder/'data.img')
cfg=(root/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','data.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((root/'media'/m[1]).resolve())+'"',cfg)
(folder/'cdos86.cfg').write_text(cfg)
commands=['c f000000']
def snapshot(name):
    commands.extend(['c 8000000','save "'+name+'.bin" bin b800:0000 fa0'])
def command(line):
    for ch in line+'\n':
        commands.extend(['key '+{' ':'Space',':':'+Shift Semicolon -Shift','\n':'Return'}.get(ch,ch),'c 200000'])
command('b:');command('user 4');command('fmview');snapshot('initial')
for keys,name in [(['F9'],'users'),(['Home','Return'],'zero'),
                  (['F9','End','Return'],'empty'),(['F9','Home','Down','Return'],'four'),
                  (['Esc'],'exit')]:
    for key in keys:commands.extend(['key '+key,'c 200000'])
    snapshot(name)
commands.append('q');before=(folder/'data.img').read_bytes()
with (folder/'pce.log').open('wb') as log:
    subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=folder,
        input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
views={}
for name in ['initial','users','zero','empty','four','exit']:
    b=(folder/(name+'.bin')).read_bytes()
    views[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
    (folder/(name+'.txt')).write_text(views[name])
assert before==(folder/'data.img').read_bytes()
assert 'U4.TXT' in views['initial'] and 'U0.TXT' not in views['initial']
assert 'User 00' in views['users'] and 'User 15' in views['users']
assert 'U0.TXT' in views['zero'] and 'U4.TXT' not in views['zero']
assert 'U0.TXT' not in views['empty'] and 'U4.TXT' not in views['empty']
assert 'U4.TXT' in views['four']
assert 'FMVIEW: closed' in views['exit'] and '4B>' in views['exit']
# A: user 0 configuration was loaded despite launch on B: user 4.
b=(folder/'initial.bin').read_bytes()
assert b[2*(1*80+1)+1]==0x71
assert b[2*(1*80+15)+1]==0x17
print('PASS: CP/M users 4/0/15, empty user, system FM.CFG, original user restored, unchanged data disk')
