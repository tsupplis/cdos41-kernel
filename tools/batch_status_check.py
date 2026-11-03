#!/usr/bin/env python3
"""Live BATCH ERRORLEVEL: native/DOS status, persistence and nested dispatch."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
FOLDER=Path(tempfile.mkdtemp(prefix="cdos-batch-status-"))
print("Diagnostics:",FOLDER,flush=True)
def run(*args):
    return subprocess.run(args,cwd=FOLDER,capture_output=True,check=True)
shutil.copyfile(ROOT/"media/diskdefs",FOLDER/"diskdefs")
run("python3",str(ROOT/"tools/cpm86twist.py"),"untwist",str(ROOT/"media/cdos86.img"),"a.logical")
run("cpmrm","-f","ccpm86-320","a.logical","0:ED.CMD","0:SDIR.CMD","0:BATCH.CMD")
run("cpmcp","-f","ccpm86-320","a.logical",str(ROOT/"commands/batch/batch.cmd"),"0:BATCH.CMD")
run("cpmchattr","-f","ccpm86-320","a.logical","s","0:BATCH.CMD")
run("mformat","-C","-i","fat.img","-t","40","-h","2","-n","8","-c","2","::")
for source in ["setenv/setenv.cmd","echo/echo.cmd"]:
    run("mcopy","-i","fat.img",str(ROOT/"commands"/source),"::")
shutil.copyfile(ROOT/"commands/batch/tests/exittest.a86",FOLDER/"ifstat.a86")
run("pcdev_rasm86","ifstat.a86")
run("pcdev_linkcmd","ifstat=ifstat[data[origin[0],max[0]]]")
run("mcopy","-i","fat.img","ifstat.cmd","::")
# Producers exercise real native termination and DOS 4Ch/INT20h paths.
for value in [0,1,7,255,256]:
    (FOLDER/'nstat.a86').write_text(f"cseg\nstart:\nmov dx,{value}\nmov cl,108\nint 0e0h\nxor dx,dx\nxor cx,cx\nint 0e0h\ndseg\norg 100h\nrs 256\nend start\n".replace('\n','\r\n'))
    run('pcdev_rasm86','nstat.a86')
    run('pcdev_linkcmd','nstat=nstat[data[origin[0],max[0]]]')
    run('mcopy','-i','fat.img','nstat.cmd',f'::N{value}.CMD')
for value in [0,1,7,255]:
    (FOLDER/'status.asm').write_text(f'bits 16\ncpu 8086\norg 100h\nmov ax,4c00h+{value}\nint 21h\n')
    run('nasm','-f','bin','status.asm','-o',f'D{value}.COM')
    run('mcopy','-i','fat.img',f'D{value}.COM','::')
(FOLDER/'oldexit.asm').write_text('bits 16\ncpu 8086\norg 100h\nint 20h\n')
run('nasm','-f','bin','oldexit.asm','-o','OLD.COM')
run('mcopy','-i','fat.img','OLD.COM','::')
# MZ wrapper around the exact same status producer verifies EXE dispatch too.
payload=(FOLDER/'D7.COM').read_bytes()
header=bytearray(32)
for offset,value in [(0,0x5a4d),(2,32+len(payload)),(4,1),(8,2),(12,0xffff),(16,0xfffe)]:
    header[offset:offset+2]=value.to_bytes(2,'little')
(FOLDER/'DX7.EXE').write_bytes(header+payload)
run('mcopy','-i','fat.img','DX7.EXE','::')
run('cpmrm','-f','ccpm86-320','a.logical','0:CCPM.SYS')
run('cpmcp','-f','ccpm86-320','a.logical',str(ROOT/'kernel/sysgen/ccpm.sys'),'0:CCPM.SYS')
run('cpmchattr','-f','ccpm86-320','a.logical','s','0:CCPM.SYS')
(FOLDER/'BAD.EXE').write_bytes(b'MZ')
run('mcopy','-i','fat.img','BAD.EXE','::')
scripts={}
for kind in ['N','D']:
    lines=['@ECHO=OFF','IF NOT ERRORLEVEL 1 ECHO InitialZero']
    for value in [7,255,1,0]:
        ext='CMD' if kind=='N' else 'COM'
        lines += [f'B:{kind}{value}.{ext}',f'IF ERRORLEVEL {value} ECHO {kind}{value}AtLeast',
                  f'IF ERRORLEVEL {value+1} ECHO WRONG-too-high' if value<255 else 'IF NOT ERRORLEVEL 255 ECHO WRONG-low',
                  'ECHO PreserveStatus',f'IF ERRORLEVEL {value} IF x==x ECHO {kind}{value}Retained']
    lines += ['IF ERRORLEVEL 1 ECHO WRONG-stale','ECHO StatusSuiteDone']
    scripts[f'ST{kind}.BAT']='\n'.join(lines)+'\n'
scripts['STFAIL.BAT']='@ECHO=OFF\nB:N7.CMD\nB:BAD.EXE\nIF ERRORLEVEL 1 ECHO RejectedOne\nIF ERRORLEVEL 2 ECHO WRONG-rejected\nB:N7.CMD\nB:ABSENT.CMD\nIF ERRORLEVEL 7 ECHO SearchPreserves\nIF ERRORLEVEL 8 ECHO WRONG-search\n'
scripts['STMIX.BAT']='@ECHO=OFF\nB:D7.COM\nIF NOT ERRORLEVEL 8 ECHO DosSeven\nB:OLD.COM\nIF ERRORLEVEL 1 ECHO WRONG-int20\nIF NOT ERRORLEVEL 1 ECHO OldExitZero\nB:DX7.EXE\nIF ERRORLEVEL 7 ECHO ExeSeven\nIF ERRORLEVEL 8 ECHO WRONG-exe\nB:N256.CMD\nIF ERRORLEVEL 255 ECHO NativeWord\nIF ERRORLEVEL 256 ECHO WRONG-overflow\nIF ERRORLEVEL 255 ECHO SyntaxPreserves\nGOTO NEXT\nECHO WRONG-goto\n:NEXT\nIF ERRORLEVEL 255 ECHO GotoPreserves\nB:CHAIN.BAT\n'
scripts['CHAIN.BAT']='@ECHO=OFF\nIF ERRORLEVEL 255 ECHO ChainPreserves\nIF ERRORLEVEL 255 EXIT 23\nECHO WRONG-exit\n'
for name,body in scripts.items():
    (FOLDER/name).write_bytes(body.replace("\n","\r\n").encode()+b"\x1a")
    run("cpmcp","-f","ccpm86-320","a.logical",name,"0:")
    if name in ["STN.BAT","STD.BAT","CHAIN.BAT"]:
        run("mcopy","-i","fat.img",name,"::")
run("python3",str(ROOT/"tools/cpm86twist.py"),"twist","a.logical","cdos86.img")
cfg=(ROOT/"media/cdos86.cfg").read_text().replace('driver = "sdl"','driver = "null"').replace("sdl:lowpass=5000","null").replace("cdostools.img","fat.img")
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/"media"/m[1]).resolve())+'"',cfg)
(FOLDER/"test.cfg").write_text(cfg)
commands=["c f000000"]
keys={":":"+Shift Semicolon -Shift"," ":"Space","\n":"Return"}
def command(text,label):
    for ch in text+"\n":
        commands.extend(["key "+keys.get(ch,ch),"c 200000"])
    commands.extend(["c 10000000",f'save "{label}.bin" bin b800:0000 fa0'])
for text,label in [('a:stn','native'),('a:std','dos'),('b:stn','fat-native'),('b:std','fat-dos'),('a:stfail','failures'),('a:stmix','mixed')]:
    command('cls','clear-'+label);command(text,label)
command("b:ifstat 23","status")
commands.append("q")
with (FOLDER/"pce.log").open("wb") as log:
    subprocess.run(["pce-ibmpc","-c","test.cfg","-t","null","-g","vga"],cwd=FOLDER,input=("\n".join(commands)+"\n").encode(),stdout=log,stderr=log,timeout=240,check=True)
def screen(name):
    video=(FOLDER/(name+".bin")).read_bytes()
    result="\n".join(bytes(video[i:i+160:2]).decode("cp437").rstrip() for i in range(0,3840,160))
    (FOLDER/(name+".txt")).write_text(result)
    return result
for name,kind in [('native','N'),('dos','D'),('fat-native','N'),('fat-dos','D')]:
    result=screen(name)
    for value in [7,255,1,0]:
        for suffix in ['AtLeast','Retained']:
            assert f'{kind}{value}{suffix}' in result,(name,value,suffix,result)
    assert 'InitialZero' in result and 'StatusSuiteDone' in result,(name,result)
    assert 'WRONG' not in result,(name,result)
result=screen('failures')
assert 'RejectedOne' in result and 'SearchPreserves' in result and 'WRONG' not in result,result
result=screen('mixed')
for marker in ['DosSeven','OldExitZero','ExeSeven','NativeWord','SyntaxPreserves','GotoPreserves','ChainPreserves']:
    assert marker in result,(marker,result)
assert 'WRONG' not in result,result
assert result.count('IF [NOT]')==1,result
assert 'BATCH EXIT PASS' in screen('status'),screen('status')
print('PASS: ERRORLEVEL native CMD and DOS COM/EXE on CP/M/FAT scripts, >=/NOT, repeated tests, built-ins/GOTO/chain persistence, INT20h reset, native word status and EXIT 23')
shutil.rmtree(FOLDER)
