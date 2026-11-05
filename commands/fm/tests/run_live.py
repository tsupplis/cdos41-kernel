"""Native/DOS/BAT Run and external Edit dispatch on disposable images."""
from pathlib import Path
import argparse,re,shutil,struct,subprocess,tempfile,sys
from pce import PCE
p=argparse.ArgumentParser();p.add_argument('--boot-image',type=Path,required=True)
a=p.parse_args();R=Path(__file__).resolve().parents[3]
F=Path(tempfile.mkdtemp(prefix='fm-run-'));print(F,flush=True)
def run(*cmd):
 r=subprocess.run(cmd,cwd=F,capture_output=True,timeout=30)
 if r.returncode:raise RuntimeError(str(cmd)+': '+(r.stdout+r.stderr).decode(errors='replace'))
 return r.stdout
def twist(mode,src,dst):run(sys.executable,str(R/'tools/cpm86twist.py'),mode,str(F/src),str(F/dst))
child="""        cseg
start:
        mov dx,offset marker
        mov cl,22
        int 0e0h
        mov dx,offset marker
        mov cl,16
        int 0e0h
        xor dx,dx
        mov cl,108
        int 0e0h
        xor cx,cx
        xor dx,dx
        int 0e0h
        dseg
        org 100h
marker  db 2,'MARKERNAME'
        db 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
        rs 256
        end start
"""
def assemble(name,source):
 (F/(name+'.a86')).write_bytes(source.replace('\n','\r\n').encode())
 output=run('pcdev_rasm86',name+'.a86')
 listing=(F/(name+'.lst')).read_text(errors='replace')
 assert re.search(r'Number of errors:\s+0\.',listing),listing
 assert (F/(name+'.obj')).is_file() and (F/(name+'.obj')).stat().st_size>0
 output+=run('pcdev_linkcmd',name+'='+name+'[data[origin[0],max[0]]]')
 assert not re.search(rb'undefined|unresolved|fatal',output,re.I),output
 assert (F/(name+'.cmd')).is_file() and (F/(name+'.cmd')).stat().st_size>128
for name,marker in [('atest','ZCMD    OK '),('zbseed','ZBAT    OK ')]:
 assemble(name,child.replace('MARKERNAME',marker))
# The mock editor preserves its complete native command-tail record as proof
# of execution and argument delivery; it never opens the selected source file.
editor=child.replace('MARKERNAME','ZEDIT   ARG').replace('        mov dx,offset marker\n        mov cl,16','        mov dx,80h\n        mov cl,26\n        int 0e0h\n        mov dx,offset marker\n        mov cl,21\n        int 0e0h\n        mov dx,offset marker\n        mov cl,16')
assemble('dredix',editor)
for name,marker in [('function','ZFUNC   ARG'),('setport','ZPORT   ARG'),
                    ('setup','ZSETUP  ARG'),('hdmaint','ZHD     ARG')]:
 assemble(name,editor.replace('ZEDIT   ARG',marker))
shutil.copy(a.boot_image,F/'cdos86.img');shutil.copy(R/'media/diskdefs',F/'diskdefs')
twist('untwist','cdos86.img','boot.logical')
# Use the reconstructed native BATCH runner, never a DOS compatibility layer.
listing=run('cpmls','-f','ccpm86-320','boot.logical').decode().upper()
if 'BATCH.CMD' in listing:run('cpmrm','-f','ccpm86-320','boot.logical','0:BATCH.CMD')
run('cpmcp','-f','ccpm86-320','boot.logical',str(R/'commands/batch/batch.cmd'),'0:BATCH.CMD')
run('cpmchattr','-f','ccpm86-320','boot.logical','s','0:BATCH.CMD');twist('twist','boot.logical','cdos86.img')
(F/'BTEST.BAT').write_bytes(b'@ECHO=OFF\r\nB:ZBSEED.CMD\r\nEXIT 0\r\n\x1a')
def dos_child(marker,origin,exitcode,exe=False,prefix=b''):
 # DOS 2 create/truncate, close and terminate. EXE DS initially addresses PSP.
 code=bytearray(b'\x0e\x1f' if exe else b'');code.extend(prefix)
 code.extend(b'\xba\0\0');operand=len(code)-2
 code.extend(b'\x31\xc9\xb4\x3c\xcd\x21\x72\0');failure=len(code)-1
 code.extend(b'\x89\xc3\xb4\x3e\xcd\x21')
 done=len(code);code.extend(bytes([0xb8,exitcode,0x4c,0xcd,0x21]))
 struct.pack_into('<H',code,operand,origin+len(code))
 code[failure]=done-(failure+1)
 code.extend(('B:'+marker).encode()+b'\0')
 assert code[failure]<128 and struct.unpack_from('<H',code,operand)[0]==origin+len(code)-len(marker)-3
 return bytes(code)
com=dos_child('ZCOM.OK',0x100,7);(F/'CCOM.COM').write_bytes(com)
# DOS E0 intercept forwards non-termination calls to native BDOS. Preserve
# DOS DS/ES around console detach (147) and delay (141, DX=2 ticks).
# The bridge must keep this exact child alive until it creates its marker.
detach=bytes.fromhex('1e06 b99300 31d2 cde0 071f 1e06 b98d00 ba0200 cde0 071f')
(F/'DDET.COM').write_bytes(dos_child('ZDET.OK',0x100,11,prefix=detach))
exe=dos_child('ZEXE.OK',0,9,True);size=32+len(exe)
# Single load module, two-paragraph header, no relocation table, CS:IP=0:0;
# 256 extra paragraphs provide the SS:SP=0:1000h stack without huge allocation.
header=struct.pack('<14H',0x5a4d,size%512,(size+511)//512,0,2,0x100,0x100,0,0x1000,0,0,0,28,0)+bytes(4)
assert len(header)==32 and struct.unpack_from('<H',header,8)[0]*16==32
assert struct.unpack_from('<H',header,4)[0]*512-(512-size%512)%512==size
(F/'CEXE.EXE').write_bytes(header+exe)
# Claims a 65535-page image, but supplies no load module. Must reject cleanly.
bad=bytearray(header);struct.pack_into('<H',bad,4,65535)
(F/'DBAD.EXE').write_bytes(bad)
(F/'ETYPE.TXT').write_bytes(b'Not executable\r\n\x1a')
run('mformat','-C','-i','data.img','-t','40','-h','2','-n','8','-c','2','::')
expected={}
for file in [R/'commands/fm/fmview.cmd',F/'atest.cmd',F/'zbseed.cmd',F/'dredix.cmd',F/'function.cmd',F/'setport.cmd',F/'setup.cmd',F/'hdmaint.cmd',F/'BTEST.BAT',F/'CCOM.COM',F/'CEXE.EXE',F/'DBAD.EXE',F/'DDET.COM',F/'ETYPE.TXT']:
 expected[file.name.upper()]=file.read_bytes();run('mcopy','-i','data.img',str(file),'::')
cfg=(R/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('driver      = "sdl:lowpass=5000"','driver      = "null"').replace('cdostools.img','data.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((R/'media'/m[1]).resolve())+'"',cfg);(F/'cdos86.cfg').write_text(cfg)
labels=[]
ready={
 'loader_failed':['FMVIEW.CMD','Cannot launch command'],
 'bad_type':['Bad file type, only .CMD, .COM, .EXE, or .BAT files'],
 'multiple':['Please select one file'],
 'native_return':['FMVIEW.CMD','ZCMD.OK'], 'native_again':['FMVIEW.CMD','ZCMD.OK'],
 'com_return':['FMVIEW.CMD','ZCOM.OK'], 'com_again':['FMVIEW.CMD','ZCOM.OK'],
 'exe_return':['FMVIEW.CMD','ZEXE.OK'], 'exe_again':['FMVIEW.CMD','ZEXE.OK'],
 'detach_return':['FMVIEW.CMD','ZDET.OK'], 'batch_return':['FMVIEW.CMD','ZBAT.OK'],
 'edit_return':['FMVIEW.CMD','ZEDIT.ARG'], 'chain_return':['FMVIEW.CMD','ZFUNC.ARG','ZSETUP.ARG'],
 'boot_prompt':['Hard disk partition type? (DOS or CP/M)'],
 'boot_invalid':['Hard disk partition type? (DOS or CP/M)'],
 'boot_empty':['FMVIEW.CMD'], 'boot_cancel':['FMVIEW.CMD'],
 'boot_return':['FMVIEW.CMD','ZHD.ARG'], 'navigate':['ATEST.CMD','BTEST.BAT'],
 'exit':['FMVIEW: closed','B>']}
launch_errors=['DOS COM/EXE launch is not supported','console error','Cannot launch',
               'Unable to launch','Program not found','Command not found']
with PCE(F,timeout=180) as vm:
 def keys(*seq):
  for k in seq:vm.key(k)
 def command(s):
  for ch in s:keys({' ': 'Space',':':'+Shift Semicolon -Shift'}.get(ch,ch))
  keys('Return')
 def snap(name):
  labels.append(name)
  errors=launch_errors if name.endswith(('_return','_again')) else ()
  vm.snapshot(name,ready[name],errors)
 def execute():keys('Tab','Home',*(['Down']*11),'Return')
 vm.wait('boot A prompt',['A>'],timeout=30)
 command('b:');vm.wait('B prompt',['B>']);command('fmview');vm.wait('FM ready',['FMVIEW.CMD','Run  a Program'])
 # First reject a malformed DOS image; later launches prove the failure cleaned up.
 keys('Home',*(['Right']*4));execute();snap('loader_failed')
 keys('Delete','Right','Right','Right');execute();snap('bad_type');keys('Delete')
 keys('Home','Comma','Right','Comma');execute();snap('multiple')
 keys('Delete','Home','Delete');execute();snap('native_return')
 keys('Home','Right','Right');execute();snap('com_return')
 keys('Home','Right','Right','Right');execute();snap('exe_return')
 # Alternate native and DOS formats again to expose stale loader/process state.
 keys('Home');execute();snap('native_again')
 keys('Home','Right','Right');execute();snap('com_again')
 keys('Home','Right','Right','Right');execute();snap('exe_again')
 keys('Home',*(['Right']*5));execute();snap('detach_return')
 keys('Home','Right');execute();snap('batch_return')
 keys('Home',*(['Right']*7),'Comma');keys('Tab','Home',*(['Down']*10),'Return')
 snap('edit_return')
 # Setup menu Assign Func Keys chains the harmless FUNCTION mock into SETUP.
 keys('Tab','Home',*(['Down']*16),'Return','Home',*(['Down']*4),'Return')
 snap('chain_return')
 def boot():keys('Tab','Home',*(['Down']*8),'Return')
 boot();snap('boot_prompt');keys('Return');snap('boot_empty')
 boot();keys('Esc');snap('boot_cancel')
 boot();command('other');snap('boot_invalid');command('dos')
 snap('boot_return')
 keys('F9','Esc');snap('navigate');keys('Esc');snap('exit')
screens={};vga={}
for name in labels:
 b=(F/(name+'.bin')).read_bytes();vga[name]=b;screens[name]='\n'.join(bytes(b[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160));(F/(name+'.txt')).write_text(screens[name])
assert 'FMVIEW.CMD' in screens['loader_failed'] and 'DBAD.EXE' in screens['loader_failed']
assert 'ZCOM.OK' not in screens['loader_failed'] and 'ZEXE.OK' not in screens['loader_failed']
for state in ['com_return','com_again']:assert 'ZCOM.OK' in screens[state] and 'FMVIEW.CMD' in screens[state]
for state in ['exe_return','exe_again']:assert 'ZEXE.OK' in screens[state] and 'FMVIEW.CMD' in screens[state]
assert 'ZCMD.OK' in screens['native_again']
assert 'ZDET.OK' in screens['detach_return'] and 'FMVIEW.CMD' in screens['detach_return']
assert 'Bad file type, only .CMD, .COM, .EXE, or .BAT files' in screens['bad_type']
assert 'Please select one file' in screens['multiple']
assert 'ZCMD.OK' in screens['native_return'] and 'ZBAT.OK' not in screens['native_return']
assert 'ZCMD.OK' in screens['batch_return'] and 'ZBAT.OK' in screens['batch_return']
assert 'ZEDIT.ARG' in screens['edit_return'] and 'ETYPE.TXT' in screens['edit_return']
assert 'ZFUNC.ARG' in screens['chain_return'] and 'ZSETUP.ARG' in screens['chain_return']
assert 'Hard disk partition type? (DOS or CP/M)' in screens['boot_prompt']
for state in ['boot_empty','boot_cancel','boot_invalid']:assert 'ZHD.ARG' not in screens[state]
assert 'Hard disk partition type? (DOS or CP/M)' in screens['boot_invalid']
assert 'ZHD.ARG' in screens['boot_return']
assert 'ATEST.CMD' in screens['navigate'] and 'BTEST.BAT' in screens['navigate']
assert 'FMVIEW: closed' in screens['exit'] and 'B>' in screens['exit']
for name,data in expected.items():assert run('mtype','-i','data.img','::'+name)==data,name
listing=run('mdir','-b','-i','data.img','::').decode().upper()
assert all(name in listing for name in ['ZCMD.OK','ZBAT.OK','ZCOM.OK','ZEXE.OK','ZDET.OK','ZEDIT.ARG'])
for name in ['ZCMD.OK','ZBAT.OK','ZCOM.OK','ZEXE.OK','ZDET.OK']:assert run('mtype','-i','data.img','::'+name)==b''
captured=run('mtype','-i','data.img','::ZEDIT.ARG')
assert len(captured)==128
argument=captured[1:1+captured[0]].strip().upper()
assert argument==b'ETYPE.TXT',argument
for name,want in [('ZFUNC.ARG',b''),('ZSETUP.ARG',b'/PARAM'),('ZHD.ARG',b'[F5,F6,F0,F0]')]:
 captured=run('mtype','-i','data.img','::'+name)
 assert len(captured)==128
 argument=captured[1:1+captured[0]].strip().upper()
 assert argument==want,(name,argument)
print('PASS: Run native/DOS/BAT markers, alternating loader cleanup, detached-child completion, malformed EXE refusal, external Edit/chain/boot arguments, unchanged source files and clean exit')
print('PCE: %.2fs, %d short polls, %d cycles' % (vm.elapsed,vm.polls,vm.cycles))
