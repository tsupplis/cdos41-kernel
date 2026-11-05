"""Read-only PCE smoke test; disposable images, bounded subprocess lifetime."""
from pathlib import Path
import tempfile,shutil,subprocess,re,argparse
parser=argparse.ArgumentParser()
parser.add_argument("--config",choices=["none","release","custom"],default="none")
mode=parser.parse_args().config
R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fmview-live-'));print(F,flush=True)
def run(*a):return subprocess.run(a,cwd=F,check=True,capture_output=True)
shutil.copyfile(R/'media/cdos86.img',F/'cdos86.img')
run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
run('mcopy','-i','fat.img',str(R/'commands/fm/fmview.cmd'),'::')
if mode!='none':
 p=F/'fm.cfg'
 p.write_bytes((R/'extra/fm.cfg').read_bytes() if mode=='release' else
     b'MENU POSITION=3\r\nOBJECT FG COLOR=7\r\nOBJECT BG COLOR=1\r\n\x1a')
 run('mcopy','-i','fat.img',str(p),'::')
for i in range(90):
 p=F/('f%07d.txt'%i);p.write_text('Read only FM test\r\n');run('mcopy','-i','fat.img',str(p),'::')
run('mmd','-i','fat.img','::SUBDIR')
p=F/'child.txt';p.write_text('Child directory fixture\r\n')
run('mcopy','-i','fat.img',str(p),'::SUBDIR/CHILD.TXT')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','fat.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg)
(F/'cdos86.cfg').write_text(cfg)
c=['c f000000']
def snap(label):c.extend(['c 8000000',f'save "{label}.bin" bin b800:0000 fa0'])
def command(s):
 for ch in s+'\n':c.extend(['key '+{':':'+Shift Semicolon -Shift','\n':'Return'}.get(ch,ch),'c 200000'])
command('b:');command('fmview');snap('initial')
for key in ['Right','Down','End','Home']:
 c.extend(['key '+key,'c 200000']);snap(key.lower())
for key,label in [('Tab','menu'),('Down','menu_down'),('End','setup_entry'),
                  ('Return','setup'),('End','setup_end'),('Esc','menu_back'),('Esc','files_back')]:
 c.extend(['key '+key,'c 200000']);snap(label)
for key,label in [('F9','directories'),('Return','child'),('F9','parent_list'),
                  ('End','parent_selected'),('Return','parent_return'),
                  ('Tab','menu_again'),('Home','first_action'),('Down','directory_action'),
                  ('Return','menu_directories'),('Esc','cancel_directory')]:
 c.extend(['key '+key,'c 200000']);snap(label)
c.extend(['key Esc']);snap('exit')
command('dir fmview.cmd');snap('shell_directory');c.append('q')
before=(F/'fat.img').read_bytes()
with (F/'pce.log').open('wb') as log:
 subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={}
for label in ['initial','right','down','end','home','menu','menu_down','setup_entry','setup','setup_end','menu_back','files_back','directories','child','parent_list','parent_selected','parent_return','menu_again','first_action','directory_action','menu_directories','cancel_directory','exit','shell_directory']:
 b=(F/(label+'.bin')).read_bytes();s='\n'.join(bytes(b[j:j+160:2]).decode('cp437').rstrip() for j in range(0,3840,160));(F/(label+'.txt')).write_text(s);screens[label]=s
assert before==(F/'fat.img').read_bytes(), 'Browser changed FAT image'
assert 'FMVIEW: closed' in screens['exit'] and 'B>' in screens['exit']
assert 'F0000000.TXT' in screens['initial']
assert 'F0000016.TXT' in screens['end'] and 'FMVIEW.CMD' in screens['end']
assert 'F0000000.TXT' in screens['home']
def attribute(label,row,col):
 return (F/(label+'.bin')).read_bytes()[2*(row*80+col)+1]
column=21 if mode=='custom' else 1
selected=attribute('initial',1,column)
assert selected!=attribute('initial',1,column+14), 'Selection not highlighted'
assert attribute('right',1,column+14)==selected and attribute('right',1,column)!=selected
assert attribute('down',2,column+14)==selected and attribute('down',1,column+14)!=selected
assert attribute('end',19,column+(42 if mode!='none' else 28))==selected
assert attribute('home',1,column)==selected
print('PASS: live FAT listing, arrows, End scrolling, Home, Escape and unchanged disk')

assert attribute('initial',1,column+14)==(0x17 if mode=='custom' else 0x30)
assert selected==(0x71 if mode=='custom' else 3)
print('PASS: configuration '+mode+'; expected pane position and colours')

menu_column=1 if mode=='custom' else 61
assert attribute('menu',1,menu_column)==2
assert attribute('menu_down',2,menu_column)==2
assert 'Change to another file directory' in screens['menu_down']
assert 'Copy to Sys Disk' in screens['setup']
assert 'Diskette  Maint' in screens['setup_end']
assert attribute('setup_end',11,menu_column)==2
assert 'Set Up System' in screens['menu_back']
assert attribute('menu_back',17,menu_column)==2
assert attribute('files_back',17,menu_column)==0x20
print('PASS: live Tab/menu arrows, setup submenu, Escape back through both panes')

assert 'SUBDIR' in screens['directories'] and 'F0000000.TXT' not in screens['directories']
assert 'CHILD.TXT' in screens['child'] and 'FMVIEW.CMD' not in screens['child']
assert '..' in screens['parent_list']
assert 'F0000000.TXT' in screens['parent_return']
assert 'SUBDIR' in screens['menu_directories'] and 'F0000000.TXT' not in screens['menu_directories']
assert 'F0000000.TXT' in screens['cancel_directory']
assert 'FMVIEW' in screens['shell_directory'] and 'CHILD' not in screens['shell_directory']
print('PASS: F9 and menu directory selection, child entry, dot-dot return, cancellation, shell mapping unchanged')
