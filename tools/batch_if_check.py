#!/usr/bin/env python3
"""Native BATCH IF on disposable CP/M and FAT images, including path isolation."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FOLDER = Path(tempfile.mkdtemp(prefix="cdos-batch-if-"))
print("Diagnostics:", FOLDER, flush=True)

def run(*args):
    return subprocess.run(args,cwd=FOLDER,check=True,capture_output=True)
shutil.copyfile(ROOT/"media/diskdefs",FOLDER/"diskdefs")
run("python3",str(ROOT/"tools/cpm86twist.py"),"untwist",str(ROOT/"media/cdos86.img"),"a.logical")
run("cpmrm","-f","ccpm86-320","a.logical","0:ED.CMD","0:SDIR.CMD","0:BATCH.CMD")
run("cpmcp","-f","ccpm86-320","a.logical",str(ROOT/"commands/batch/batch.cmd"),"0:BATCH.CMD")
run("cpmchattr","-f","ccpm86-320","a.logical","s","0:BATCH.CMD")
run("mformat","-C","-i","fat.img","-t","40","-h","2","-n","8","-c","2","::")
for directory in ["SUB","EMPTY","SUB/DEEP","SUB/ONLYDIR"]:
    run("mmd","-i","fat.img","::"+directory)
for name,body in [("ROOT.TXT",b"root"),("ZERO.DAT",b""),("HIDE.SYS",b"hidden"),("SUB/INNER.DAT",b"inner"),("SUB/DEEP/LEAF.TXT",b"leaf")]:
    (FOLDER/"fixture").write_bytes(body)
    run("mcopy","-i","fat.img","fixture","::"+name)
run("mattrib","-i","fat.img","+h","+s","+r","::HIDE.SYS")
(FOLDER/"known.txt").write_bytes(b"CPM\r\n\x1a")
run("cpmcp","-f","ccpm86-320","a.logical","known.txt","0:KNOWN.TXT")
(FOLDER/"zero.dat").write_bytes(b"")
run("cpmcp","-f","ccpm86-320","a.logical","zero.dat","0:ZERO.DAT")

cases = [
    ("EXIST A:KNOWN.TXT",True),("EXIST A:MISSING.TXT",False),("EXIST A:*.TXT",True),("EXIST A:ZERO.DAT",True),
    ("DIREXIST A:KNOWN.TXT",False),("DIREXIST A:*.*",False),
    ("EXIST B:ROOT.TXT",True),("EXIST B:ZERO.DAT",True),("EXIST B:HIDE.SYS",True),("EXIST B:SUB",False),
    (r"EXIST B:\sub\inner.dat",True),("EXIST B:SUB/INNER.DAT",True),
    (r"EXIST B:SUB\DEEP\..\INNER.DAT",True),(r"EXIST B:SUB\.\INNER.DAT",True),
    (r"EXIST B:SUB\DEEP\*.TXT",True),(r"EXIST B:SUB\*.TXT",False),
    (r"EXIST B:\ABSENT\*.*",False),(r"EXIST B:ROOT.TXT\ANY.TXT",False),
    ("DIREXIST B:\\",True),("DIREXIST B:",True),("EXIST B:\\",False),
    ("DIREXIST B:SUB",True),(r"DIREXIST B:\EMPTY",True),(r"DIREXIST B:SUB\DEEP",True),
    (r"DIREXIST B:SUB\DEEP\..",True),("DIREXIST B:SUB\\.\\",True),
    ("DIREXIST B:SUB\\DEEP\\",True),(r"DIREXIST B:SUB\*.*",True),
    (r"DIREXIST B:SUB\*.TXT",False),("DIREXIST B:ROOT.TXT",False),("DIREXIST B:ABSENT",False),
    ("DIREXIST B:.",True),("DIREXIST B:..",True),
    (r"EXIST B:\..\ROOT.TXT",True),
]
expected = {}
launches = []
def script(name,body,fat=False):
    (FOLDER/name).write_bytes(body.encode()+b"\x1a")
    if fat:
        run("mcopy","-i","fat.img",name,"::")
    else:
        run("cpmcp","-f","ccpm86-320","a.logical",name,"0:")
for start in range(0,len(cases),6):
    name=f"IF{start//6}.BAT"; body="@ECHO=OFF\r\n"; markers=[]
    for number,(predicate,value) in enumerate(cases[start:start+6],start):
        body+=f"IF {predicate} ECHO CASE{number}-YES\r\nIF NOT {predicate} ECHO CASE{number}-NO\r\n"
        markers.append(f"CASE{number}-"+("YES" if value else "NO"))
    body+="ECHO GROUP-DONE\r\n"; script(name,body)
    label=f"group{start//6}"; launches.append(("a:"+name[:-4].lower(),label)); expected[label]=markers
# Same parser on a FAT-hosted script; body command names and text retain case.
script("IFFAT.BAT","@ECHO=OFF\r\nIF EXIST B:ROOT.TXT ECHO FAT-SCRIPT-PASS\r\nIF NOT DIREXIST B:ROOT.TXT ECHO FILE-IS-NOT-DIR\r\n",True)
launches.append(("b:iffat","fat-script")); expected["fat-script"]=["FAT-SCRIPT-PASS","FILE-IS-NOT-DIR"]
# Malformed syntax/invalid drives never become true through NOT.
script("IFBAD.BAT",'@ECHO=OFF\r\nIF\r\nIF NOT\r\nIF EXISTS A:KNOWN.TXT ECHO WRONG\r\nIF EXIST\r\nIF EXIST A:KNOWN.TXT\r\nIF=EXIST A:KNOWN.TXT ECHO WRONG\r\nIF NOT EXIST Z:BAD ECHO WRONG\r\nIF NOT EXIST B:SUB*\\LEAF.TXT ECHO WRONG\r\nIF NOT EXIST "B:ROOT.TXT" ECHO WRONG\r\nIF NOT EXIST L:BAD ECHO WRONG\r\nECHO BAD-SYNTAX-DONE\r\n')
launches.append(("a:ifbad","bad"))
# Conditional text is not expanded a second time. Existing built-ins, native
# CMDs, drive changes, GOTO and EXIT use the original dispatch paths.
run("mcopy","-i","fat.img",str(ROOT/"commands/echo/echo.cmd"),"::")
run("mcopy","-i","fat.img",str(ROOT/"commands/setenv/setenv.cmd"),"::")
script("IFEXEC.BAT","@ECHO=OFF\r\nB:SETENV Target=B:\\SUB\\INNER.DAT\r\nB:SETENV Message=Literal%%UNEXPANDED%%\r\nIF EXIST %Target% ECHO %Message%\r\niF nOt ExIsT B:missing IF DIREXIST B:SUB ECHO NestedCase\r\nIF EXIST A:KNOWN.TXT B:ECHO.CMD ChildCase\r\nIF EXIST A:KNOWN.TXT B:\r\nIF EXIST ROOT.TXT ECHO DRIVE-PASS\r\nIF EXIST A:KNOWN.TXT GOTO END\r\nECHO WRONG-GOTO\r\n:END\r\nIF EXIST A:KNOWN.TXT EXIT 7\r\nECHO WRONG-EXIT\r\n")
launches.append(("a:ifexec","execute"))
# Keep B: and all floating aliases mapped while absolute/relative tests run.
script("IFMAP.BAT","@ECHO=OFF\r\nIF EXIST B:INNER.DAT ECHO RELATIVE-PASS\r\nIF EXIST B:\\ROOT.TXT ECHO ABSOLUTE-PASS\r\nIF EXIST B:INNER.DAT ECHO RESTORED-PASS\r\nIF NOT EXIST B:\\ABSENT\\ANY.TXT ECHO MISSING-PATH-PASS\r\nIF EXIST B:INNER.DAT ECHO ERROR-RESTORE-PASS\r\nIF EXIST N:LEAF.TXT ECHO N-RELATIVE-PASS\r\nIF EXIST N:\\ROOT.TXT ECHO N-ABSOLUTE-PASS\r\nIF EXIST N:LEAF.TXT ECHO N-RESTORED-PASS\r\nIF EXIST O:INNER.DAT ECHO O-PASS\r\nIF EXIST P:KNOWN.TXT ECHO P-PASS\r\nECHO MAPPING-DONE\r\n")
# Repeated path probes must reuse their private mapping, not leak descriptors.
script("IFLOOP.BAT","@ECHO=OFF\r\n"+"IF EXIST B:\\SUB\\DEEP\\LEAF.TXT REM matched\r\n"*160+"IF EXIST B:INNER.DAT ECHO LOOP-RESTORED\r\nECHO LOOP-DONE\r\n")
run("python3",str(ROOT/"tools/cpm86twist.py"),"twist","a.logical","cdos86.img")
cfg=(ROOT/"media/cdos86.cfg").read_text().replace('driver = "sdl"','driver = "null"').replace("sdl:lowpass=5000","null").replace("cdostools.img","fat.img")
cfg=re.sub(r'(?m)^path\s*=\s*"([^"\n]+)"',lambda m:'path = "'+str((ROOT/"media"/m[1]).resolve())+'"',cfg)
(FOLDER/"test.cfg").write_text(cfg)
commands=["c f000000"]
keys={":":"+Shift Semicolon -Shift"," ":"Space","\n":"Return","\\":"Backslash","=":"Equal"}
def command(text,label,cycles="10000000"):
    for ch in text+"\n":
        commands.extend(["key "+keys.get(ch,ch),"c 200000"])
    commands.extend(["c "+cycles,f'save "{label}.bin" bin b800:0000 fa0'])
for text,label in launches:
    command("cls","clear-"+label)
    command(text,label)
command("a:","return-a")
for text,label in [("chdir b:\\sub","map-b"),("chdir n:=b:\\sub\\deep","map-n"),("chdir o:=b:\\sub","map-o")]:
    command(text,label)
command("cls","clear-map");command("a:ifmap","mappings")
command("cls","clear-loop");command("a:ifloop","loop","30000000")
command("dir b:inner.dat","parent-b")
command("dir n:leaf.txt","parent-n")
command("dir o:inner.dat","parent-o")
command("dir p:known.txt","parent-p")
commands.append("q")
with (FOLDER/"pce.log").open("wb") as log:
    subprocess.run(["pce-ibmpc","-c","test.cfg","-t","null","-g","vga"],cwd=FOLDER,input=("\n".join(commands)+"\n").encode(),stdout=log,stderr=log,timeout=300,check=True)
def screen(name):
    video=(FOLDER/(name+".bin")).read_bytes()
    result="\n".join(bytes(video[i:i+160:2]).decode("cp437").rstrip() for i in range(0,3840,160))
    (FOLDER/(name+".txt")).write_text(result)
    return result
for name,markers in expected.items():
    result=screen(name)
    for marker in markers:
        assert marker in result,(name,marker,result)
    for line in result.splitlines():
        if re.fullmatch(r"CASE\d+-(YES|NO)",line): assert line in markers,(name,line,result)
    assert "IF cannot" not in result and "Invalid IF" not in result,(name,result)
bad=screen("bad");assert "WRONG" not in bad and "BAD-SYNTAX-DONE" in bad,bad
result=screen("execute")
for marker in ["Literal%UNEXPANDED%","NestedCase","ChildCase","DRIVE-PASS"]: assert marker in result,(marker,result)
assert "WRONG" not in result,result
result=screen("mappings")
for marker in ["RELATIVE-PASS","ABSOLUTE-PASS","RESTORED-PASS","MISSING-PATH-PASS","ERROR-RESTORE-PASS","N-RELATIVE-PASS","N-ABSOLUTE-PASS","N-RESTORED-PASS","O-PASS","P-PASS","MAPPING-DONE"]: assert marker in result,(marker,result)
result=screen("loop");assert "LOOP-RESTORED" in result and "LOOP-DONE" in result and "IF cannot" not in result,result
for name,filename in [("parent-b","INNER"),("parent-n","LEAF"),("parent-o","INNER"),("parent-p","KNOWN")]:
    result=screen(name);assert filename in result and "File not found" not in result,(name,result)
print(f"PASS: {len(cases)} paired EXIST/DIREXIST/NOT cases on CP/M/FAT; full/relative paths, wildcards, empty/hidden/system files, malformed syntax, missing drive, one-pass expansion, nested dispatch, GOTO/EXIT, 160 repeated probes and B:/N:/O:/P: mapping preservation")
shutil.rmtree(FOLDER)
