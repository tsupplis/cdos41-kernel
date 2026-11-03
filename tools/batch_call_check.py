#!/usr/bin/env python3
"""CALL/nested BATCH proof: return status, caller state and console ownership."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
FOLDER=Path(tempfile.mkdtemp(prefix='cdos-batch-call-'))
print('Diagnostics:',FOLDER,flush=True)
def run(*args):
    return subprocess.run(args,cwd=FOLDER,capture_output=True,check=True)
shutil.copyfile(ROOT/'media/diskdefs',FOLDER/'diskdefs')
run('python3',str(ROOT/'tools/cpm86twist.py'),'untwist',str(ROOT/'media/cdos86.img'),'a.logical')
run('cpmrm','-f','ccpm86-320','a.logical','0:ED.CMD','0:SDIR.CMD','0:BATCH.CMD','0:SHOW.CMD','0:SET.CMD','0:TYPE.CMD','0:DATE.CMD')
run('cpmcp','-f','ccpm86-320','a.logical',str(ROOT/'commands/batch/batch.cmd'),'0:BATCH.CMD')
run('cpmchattr','-f','ccpm86-320','a.logical','s','0:BATCH.CMD')
run('mformat','-C','-i','fat.img','-t','40','-h','2','-n','8','-c','2','::')
for source in ['setenv/setenv.cmd','echo/echo.cmd','batch/batch.cmd']:
    run('mcopy','-i','fat.img',str(ROOT/'commands'/source),'::')
shutil.copyfile(ROOT/'commands/batch/tests/exittest.a86',FOLDER/'forstat.a86')
run('pcdev_rasm86','forstat.a86')
run('pcdev_linkcmd','forstat=forstat[data[origin[0],max[0]]]')
run('mcopy','-i','fat.img','forstat.cmd','::')
# Test-only DOS child prints its tail, then returns status 7 through real 4Ch.
(FOLDER/'dosfor.asm').write_text('''bits 16
cpu 8086
org 100h
mov bx,1
mov dx,81h
xor cx,cx
mov cl,[80h]
mov ah,40h
int 21h
mov dx,newline
mov ah,9
int 21h
mov ax,4c07h
int 21h
newline db 13,10,'$'
''')
run('nasm','-f','bin','dosfor.asm','-o','DOSFOR.COM')
run('mcopy','-i','fat.img','DOSFOR.COM','::')
import sys
verb='B:BATCH.CMD' if '--probe' in sys.argv else 'CALL'
scripts={
'TOP.BAT':f'@ECHO=OFF\nECHO Before=[%1]\n{verb} B:CHILD.BAT MiXeD Second\nIF ERRORLEVEL 7 ECHO ChildStatus7\nIF ERRORLEVEL 8 ECHO WRONG-status\nECHO After=[%1]\nPAUSE\nCLS\nFOR %%I IN (1..2) DO {verb} B:ITER.BAT %%I\nECHO LoopReturned\nPAUSE\nCLS\n{verb} B:EMPTY.BAT\nIF NOT ERRORLEVEL 1 ECHO EofZero\nB:DOSFOR.COM ParentDos\nIF ERRORLEVEL 7 ECHO ParentDosStatus\nECHO EnvShared=[%CALLVAR%]\nECHO CallerContinues\nEXIT 23\nECHO WRONG-parent-exit\n',
'CHILD.BAT':f'@ECHO=OFF\nECHO ChildArgs=[%0][%1][%2]\nSHIFT\nECHO ChildShift=[%1]\nFOR %%J IN (A B) DO ECHO ChildLoop=%%J\n{verb} B:LEAF.BAT DeepCase\nIF ERRORLEVEL 9 ECHO LeafStatus9\nB:DOSFOR.COM ChildDos\nB:SETENV CALLVAR=SharedCase\nEXIT 7\nECHO WRONG-child-exit\n',
'LEAF.BAT':'@ECHO=OFF\nECHO LeafArg=[%1]\nEXIT 9\n',
'ITER.BAT':'@ECHO=OFF\nECHO Iteration=[%1]\nFOR %%J IN (X) DO ECHO PrivateLoop=%%J\nEXIT 0\n',
'EMPTY.BAT':'@ECHO=OFF\nB:DOSFOR.COM EofDos\n',
'CHAIN0.BAT':'@ECHO=OFF\nB:CHAIN1.BAT\nECHO WRONG-chain-return\n',
'CHAIN1.BAT':'@ECHO=OFF\nECHO ChainedChild\nEXIT 11\n',
'CPM.BAT':'@ECHO=OFF\nECHO CpmCall=[%1]\nEXIT 5\n',
'DANGER.BAT':'@ECHO=OFF\nECHO WRONG-empty-target\n',
'FAIL.BAT':"@ECHO=OFF\nCALL %CALLMISSING% B:DANGER.BAT\nIF ERRORLEVEL 1 ECHO MissingTargetOne\nCALL B:MISSING.BAT\nIF ERRORLEVEL 1 ECHO MissingOne\nCALL B:ITER.TXT\nIF ERRORLEVEL 1 ECHO TypeOne\nCALL B:*.BAT\nIF ERRORLEVEL 1 ECHO WildcardOne\nCALL :label\nIF ERRORLEVEL 1 ECHO LabelOne\nCALL\nIF ERRORLEVEL 1 ECHO EmptyOne\nECHO FailureContinues\n",
'EXTRA.BAT':f'@ECHO=OFF\n{verb} A:CPM CpCase\nIF ERRORLEVEL 5 ECHO CpmStatus5\n{verb} B:CHAIN0.BAT\nIF ERRORLEVEL 11 ECHO ChainStatus11\n{verb} b:iter.bat LowerCase\nECHO ExtraContinues\n',
}
for name,body in scripts.items():
    (FOLDER/name).write_bytes(body.replace('\n','\r\n').encode()+b'\x1a')
    run('cpmcp','-f','ccpm86-320','a.logical',name,'0:')
    if name != 'TOP.BAT':
        run('mcopy','-i','fat.img',name,'::')
run('python3',str(ROOT/'tools/cpm86twist.py'),'twist','a.logical','cdos86.img')
cfg=(ROOT/'media/cdos86.cfg').read_text().replace('driver = "sdl"','driver = "null"').replace('sdl:lowpass=5000','null').replace('cdostools.img','fat.img')
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/'media'/m[1]).resolve())+'"',cfg)
(FOLDER/'test.cfg').write_text(cfg)
commands=['c f000000']
keys={':':'+Shift Semicolon -Shift',' ':'Space','\n':'Return'}
def command(text,label):
    for ch in text+'\n': commands.extend(['key '+keys.get(ch,ch),'c 200000'])
    commands.extend(['c 10000000',f'save "{label}.bin" bin b800:0000 fa0'])
command('a:top parentcase','top')
commands.extend(['key Space','c 10000000','save "loop.bin" bin b800:0000 fa0','key Space','c 10000000','save "final.bin" bin b800:0000 fa0'])
command('b:forstat 23','status')
command('cls','clear-fail')
command('b:fail','failures')
command('cls','clear-extra')
command('b:extra','extra')
commands.append('q')
with (FOLDER/'pce.log').open('wb') as log:
    subprocess.run(['pce-ibmpc','-c','test.cfg','-t','null','-g','vga'],cwd=FOLDER,input=('\n'.join(commands)+'\n').encode(),stdout=log,stderr=log,timeout=300,check=True)
def screen(name):
    v=(FOLDER/(name+'.bin')).read_bytes()
    text='\n'.join(bytes(v[i:i+160:2]).decode('cp437').rstrip() for i in range(0,3840,160))
    (FOLDER/(name+'.txt')).write_text(text)
    return text
for name,markers in {
    'top':['Before=[parentcase]','ChildArgs=[B:CHILD.BAT][MiXeD][Second]',
           'ChildShift=[Second]','ChildLoop=A','ChildLoop=B','LeafArg=[DeepCase]',
           'LeafStatus9','ChildDos','ChildStatus7','After=[parentcase]'],
    'loop':['Iteration=[1]','Iteration=[2]','PrivateLoop=X','LoopReturned'],
    'final':['EofZero','ParentDosStatus','EnvShared=[SharedCase]','CallerContinues'],
    'failures':['MissingTargetOne','MissingOne','TypeOne','WildcardOne','LabelOne','EmptyOne','FailureContinues'],
    'extra':['CpmCall=[CpCase]','CpmStatus5','ChainedChild','ChainStatus11','Iteration=[LowerCase]','ExtraContinues'],
}.items():
    text=screen(name)
    for marker in markers: assert marker in text,(name,marker,text)
    assert 'WRONG' not in text,(name,text)
assert 'BATCH EXIT PASS' in screen('status'),screen('status')
print('PASS: CALL/nested BATCH returns after CMD/DOS children and nested calls; arguments/SHIFT/FOR isolation, shared environment, 7/9/EOF-zero status and parent EXIT 23')
shutil.rmtree(FOLDER)
