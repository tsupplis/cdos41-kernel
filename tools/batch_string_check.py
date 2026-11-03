#!/usr/bin/env python3
"""Live BATCH string comparisons, expansion and normal command dispatch."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
FOLDER=Path(tempfile.mkdtemp(prefix="cdos-batch-strings-"))
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
run("mmd","-i","fat.img","::SUB")
(FOLDER/"known.txt").write_bytes(b"CPM\r\n\x1a")
run("cpmcp","-f","ccpm86-320","a.logical","known.txt","0:KNOWN.TXT")
(FOLDER/"remove.tmp").write_bytes(b"temporary")
run("mcopy","-i","fat.img","remove.tmp","::")
# Test-only DOS program; production commands keep their normal RASM86 build.
(FOLDER/"dosif.asm").write_text("bits 16\ncpu 8086\norg 100h\nmov dx,message\nmov ah,9\nint 21h\nmov ax,4c00h\nint 21h\nmessage db 'DOS-STRING-PASS',13,10,'$'\n")
run("nasm","-f","bin","dosif.asm","-o","DOSIF.COM")
run("mcopy","-i","fat.img","DOSIF.COM","::")
shutil.copyfile(ROOT/"commands/batch/tests/exittest.a86",FOLDER/"ifstat.a86")
run("pcdev_rasm86","ifstat.a86")
run("pcdev_linkcmd","ifstat=ifstat[data[origin[0],max[0]]]")
run("mcopy","-i","fat.img","ifstat.cmd","::")
scripts={
"STEMPTY.BAT":'''@ECHO=OFF
B:SETENV NAME=
PATH=
IF "%NAME%TOTO"=="TOTO" ECHO EmptySuffix
IF NOT "%NAME%TOTO"=="TOTO" ECHO WRONG-empty
IF "%NAME%"=="" ECHO EmptyValue
IF "%PATH%"=="" ECHO EmptyExisting
IF "%UNDEFINED%"=="" ECHO Undefined
IF "" == "" ECHO QuotedEmpty
IF NOT " "=="" ECHO SpaceDiff
IF NOT abc==ABC ECHO CaseSensitive
''',
"STVALUE.BAT":'''@ECHO=OFF
B:SETENV NAME=ABC
IF "%NAME%TOTO"=="ABCTOTO" ECHO Concatenated
IF NOT "%NAME%TOTO"=="TOTO" ECHO ValueSuffix
IF "%NAME%TOTO"=="TOTO" ECHO WRONG-value
B:SETENV NAME=Mixed Case
IF "%NAME%" == "Mixed Case" ECHO SpacedValue
IF NOT "%NAME%"=="mixed case" ECHO CaseDiff
IF "abc"==abc ECHO WRONG-quotes
IF NOT "abc"==abc ECHO LiteralQuotes
IF "A==B"=="A==B" ECHO QuotedOperator
IF NOT 01==1 ECHO TextNotNumber
B:SETENV Message=Literal%%NAME%%
IF "%Message%"=="Literal%%NAME%%" ECHO OnePass
''',
"STNULL.BAT":'''@ECHO=OFF
B:SETENV MISSING=
IF %MISSING% == VALUE ECHO WRONG-left
IF VALUE == %MISSING% ECHO WRONG-right
IF %MISSING%==VALUE ECHO WRONG-left-tight
IF VALUE==%MISSING% ECHO WRONG-right-tight
IF x==x IF VALUE==%MISSING% ECHO WRONG-nested
IF "%MISSING%"=="" ECHO QuotedMissing
IF "%MISSING%TOTO"=="TOTO" ECHO MissingSuffix
ECHO EmptyErrorsContinue
''',
"STEXEC.BAT":'''@ECHO=OFF
IF EXIST A:KNOWN.TXT IF "a"=="a" ECHO FileThenString
IF "a"=="a" IF DIREXIST B:SUB ECHO StringThenDir
IF x==x IF NOT x==X ECHO NestedMixedCase
IF x==X IF nonsense ECHO WRONG-nested
IF "x"=="x" B:ECHO.CMD ChildCase
IF x==x B:DOSIF.COM
IF x==x DEL B:REMOVE.TMP
IF NOT EXIST B:REMOVE.TMP ECHO AliasPass
IF x==x B:
IF EXIST SUB ECHO WRONG-directory
IF DIREXIST SUB ECHO DrivePass
IF x==x GOTO END
ECHO WRONG-goto
:END
IF x==x EXIT 23
ECHO WRONG-exit
''',
"STBAD.BAT":'''@ECHO=OFF
IF ==a ECHO WRONG-left
IF a=b ECHO WRONG-single
IF a!=b ECHO WRONG-operator
IF a==a
IF "a==a ECHO WRONG-quote
IF a=="a ECHO WRONG-right
IF a b==a ECHO WRONG-space
IF /I a==A ECHO WRONG-case
ECHO SyntaxContinues
''',
}
for name,body in scripts.items():
    (FOLDER/name).write_bytes(body.replace("\n","\r\n").encode()+b"\x1a")
    run("cpmcp","-f","ccpm86-320","a.logical",name,"0:")
    if name in ["STEMPTY.BAT","STVALUE.BAT"]:
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
for text,label in [("a:stempty","cpm-empty"),("a:stvalue","cpm-value"),("b:stempty","fat-empty"),("b:stvalue","fat-value"),("a:stbad","syntax"),("a:stnull","empty-errors"),("a:stexec","execute")]:
    command("cls","clear-"+label);command(text,label)
command("b:ifstat 23","status")
commands.append("q")
with (FOLDER/"pce.log").open("wb") as log:
    subprocess.run(["pce-ibmpc","-c","test.cfg","-t","null","-g","vga"],cwd=FOLDER,input=("\n".join(commands)+"\n").encode(),stdout=log,stderr=log,timeout=240,check=True)
def screen(name):
    video=(FOLDER/(name+".bin")).read_bytes()
    result="\n".join(bytes(video[i:i+160:2]).decode("cp437").rstrip() for i in range(0,3840,160))
    (FOLDER/(name+".txt")).write_text(result)
    return result
for name in ["cpm-empty","fat-empty"]:
    result=screen(name)
    for marker in ["EmptySuffix","EmptyValue","EmptyExisting","Undefined","QuotedEmpty","SpaceDiff","CaseSensitive"]:
        assert marker in result,(name,marker,result)
    assert "WRONG" not in result,(name,result)
for name in ["cpm-value","fat-value"]:
    result=screen(name)
    for marker in ["Concatenated","ValueSuffix","SpacedValue","CaseDiff","LiteralQuotes","QuotedOperator","TextNotNumber","OnePass"]:
        assert marker in result,(name,marker,result)
    assert "WRONG" not in result,(name,result)
result=screen("syntax");assert "SyntaxContinues" in result and "WRONG" not in result,result
assert result.count("IF [NOT]")==8,result
result=screen("empty-errors")
assert result.count("IF [NOT]")==5,result
for marker in ["QuotedMissing","MissingSuffix","EmptyErrorsContinue"]:
    assert marker in result,(marker,result)
assert "WRONG" not in result,result
result=screen("execute")
for marker in ["FileThenString","StringThenDir","NestedMixedCase","ChildCase","DOS-STRING-PASS","AliasPass","DrivePass"]:
    assert marker in result,(marker,result)
assert "WRONG" not in result,result
assert "BATCH EXIT PASS" in screen("status"),screen("status")
print("PASS: native string IF on CPM/FAT scripts; undefined/empty/value plus TOTO, case/quote/space/operator semantics, single expansion, mixed nested predicates, native/DOS/alias/drive dispatch, GOTO, syntax recovery and EXIT 23")
shutil.rmtree(FOLDER)
