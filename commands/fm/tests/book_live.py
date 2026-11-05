"""Session directory bookmarks on isolated FAT and CP/M media."""
from pathlib import Path
import argparse,re,shutil,subprocess,tempfile,sys
p=argparse.ArgumentParser();p.add_argument('--boot-image',type=Path,required=True)
p.add_argument('--media',choices=['fat','cpm'],required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fm-book-'+a.media+'-'));print(F,flush=True)
shutil.copy(a.boot_image,F/'cdos86.img');shutil.copy(R/'media/diskdefs',F/'diskdefs')
def run(*cmd):
 r=subprocess.run(cmd,cwd=F,capture_output=True,timeout=30)
 if r.returncode:raise RuntimeError(str(cmd)+': '+r.stderr.decode(errors='replace'))
 return r.stdout
def twist(mode,src,dst):run(sys.executable,str(R/'tools/cpm86twist.py'),mode,str(F/src),str(F/dst))
payload=bytes(range(256));(F/'AONE.BIN').write_bytes(payload)
program=(R/'commands/fm/fmview.cmd').read_bytes()
markers={'SUBONLY.TXT':b'Sub directory'.ljust(128,b'!'),
 'OTHER.TXT':b'Other directory'.ljust(128,b'?'),
 'DEEPONLY.TXT':b'Deep directory'.ljust(128,b'#')}
for name,data in markers.items():(F/name).write_bytes(data)
if a.media=='fat':
 run('mformat','-C','-i','data.img','-t','40','-h','2','-n','8','-c','2','::')
 for d in ['SUB','OTHER','SUB/DEEP']:run('mmd','-i','data.img','::'+d)
 for file in [R/'commands/fm/fmview.cmd',F/'AONE.BIN']:run('mcopy','-i','data.img',str(file),'::')
 for name,d in [('SUBONLY.TXT','SUB'),('OTHER.TXT','OTHER'),('DEEPONLY.TXT','SUB/DEEP')]:run('mcopy','-i','data.img',str(F/name),'::'+d)
else:
 shutil.copy(R/'media/base.img',F/'data.img');twist('untwist','data.img','data.logical');twist('untwist','cdos86.img','boot.logical')
 data=bytearray((F/'data.logical').read_bytes());data[:4096]=(F/'boot.logical').read_bytes()[:4096];(F/'data.logical').write_bytes(data)
 for file in [R/'commands/fm/fmview.cmd',F/'AONE.BIN']:run('cpmcp','-f','ccpm86-320','data.logical',str(file),'0:')
 for name,u in [('SUBONLY.TXT',1),('OTHER.TXT',2)]:run('cpmcp','-f','ccpm86-320','data.logical',str(F/name),str(u)+':')
 twist('twist','data.logical','data.img')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','data.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg);(F/'cdos86.cfg').write_text(cfg)
c=['c f000000'];labels=[]
def keys(*seq):
 for k in seq:c.extend(['key '+k,'c 1000000'])
def command(s):
 for ch in s:keys({' ': 'Space',':':'+Shift Semicolon -Shift'}.get(ch,ch))
 keys('Return')
def snap(name):labels.append(name);c.extend(['c 1000000','save "'+name+'.bin" bin b800:0000 fa0'])
def copy():keys('Tab','Home',*(['Down']*6),'Return')
command('b:');command('fmview');c.append('c 8000000')
keys('F7');snap('unset');keys('F9','Home','Right')
if a.media=='fat':keys('F4');snap('set2');keys('Right','F3');snap('set1')
else:keys('F3');snap('set1');keys('Right','F4');snap('set2')
keys('Esc','Home');copy();keys('F7');c.append('c 8000000');snap('copy1')
keys('Home');copy();keys('F8');c.append('c 8000000');snap('copy2')
keys('F7');snap('nav1')
if a.media=='fat':
 # All three aliases now hold two pinned bookmarks and the active clone.
 keys('Home');copy();keys('End','Up','Return','Home','Right','Right','Return');snap('scarce')
 keys('Esc','F9','Home','Right','Right','Return');snap('deep')
 keys('F7');snap('nav1_again')
else:
 # Visit another CP/M user through ordinary navigation, then revisit bookmark.
 keys('F9','Home','Return','F7');snap('nav1_again')
keys('F8');snap('nav2');keys('Esc');snap('exit')
command('fmview');c.append('c 8000000');snap('reopen');keys('Esc');snap('exit_again');c.append('q')
with (F/'pce.log').open('wb') as log:
 subprocess.run(['pce-ibmpc','-c','cdos86.cfg','-t','null','-g','vga'],cwd=F,input=('\n'.join(c)+'\n').encode(),stdout=log,stderr=log,timeout=90,check=True)
screens={}
for name in labels:
 b=(F/(name+'.bin')).read_bytes();screens[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160));(F/(name+'.txt')).write_text(screens[name])
assert 'first set Dir #1' in screens['unset']
assert 'DIR #1 set to:' in screens['set1'] and 'DIR #2 set to:' in screens['set2']
assert 'Copy done' in screens['copy1'] and 'Copy done' in screens['copy2']
for state in ['nav1','nav1_again']:assert 'SUBONLY.TXT' in screens[state] and 'AONE.BIN' in screens[state] and 'DEEPONLY.TXT' not in screens[state]
assert 'OTHER.TXT' in screens['nav2'] and 'AONE.BIN' in screens['nav2']
assert 'AONE.BIN' in screens['reopen'] and 'FMVIEW.CMD' in screens['reopen'] and 'SUBONLY.TXT' not in screens['reopen']
for state in ['exit','exit_again']:assert 'FMVIEW: closed' in screens[state] and 'B>' in screens[state]
if a.media=='fat':
 assert 'alias' in screens['scarce'].lower() and 'free' in screens['scarce'].lower()
 assert 'DEEPONLY.TXT' in screens['deep'] and 'SUBONLY.TXT' not in screens['deep']
 for path in ['AONE.BIN','SUB/AONE.BIN','OTHER/AONE.BIN']:assert run('mtype','-i','data.img','::'+path)==payload,path
 for name,d in [('SUBONLY.TXT','SUB'),('OTHER.TXT','OTHER'),('DEEPONLY.TXT','SUB/DEEP')]:assert run('mtype','-i','data.img','::'+d+'/'+name)==markers[name]
 assert run('mtype','-i','data.img','::FMVIEW.CMD')==program
 listing=run('mdir','-b','-s','-i','data.img','::').decode().upper()
 assert '/SUB/DEEP/AONE.BIN' not in listing and not re.search(r'FMC[PB][0-9]{4}',listing)
else:
 twist('untwist','data.img','result.logical')
 for u in [0,1,2]:
  run('cpmcp','-f','ccpm86-320','result.logical',str(u)+':AONE.BIN',str(F/'result.bin'));assert (F/'result.bin').read_bytes()==payload
 for name,u in [('SUBONLY.TXT',1),('OTHER.TXT',2)]:
  run('cpmcp','-f','ccpm86-320','result.logical',str(u)+':'+name,str(F/'result.bin'));assert (F/'result.bin').read_bytes()==markers[name]
print('PASS: '+a.media+' bookmark setting, copy destinations, immutable navigation identities, binary preservation and restored source context')
