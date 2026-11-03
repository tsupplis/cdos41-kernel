#!/usr/bin/env python3
"""HIDDEN/SYSTEM integration checks on one disposable PCE at a time."""

from pathlib import Path
import json, os, re, subprocess, sys, tempfile

R = Path(__file__).resolve().parent.parent


def run(d, *args):
    result = subprocess.run(args, cwd=d, capture_output=True)
    if result.returncode:
        raise RuntimeError((args, result.stderr.decode(errors="replace")))
    return result.stdout


def entries(image):
    b = image.read_bytes()
    sector = int.from_bytes(b[11:13], "little")
    start = (
        int.from_bytes(b[14:16], "little") + b[16] * int.from_bytes(b[22:24], "little")
    ) * sector
    return {
        b[o : o + 11]: b[o : o + 32]
        for o in range(start, start + int.from_bytes(b[17:19], "little") * 32, 32)
        if b[o] not in [0, 229]
    }


def fixture(prefix):
    d = Path(tempfile.mkdtemp(prefix=prefix))
    print("Diagnostics:", d, flush=True)
    (d / "cdos86.img").write_bytes(Path(os.environ.get("HIDDEN_TEST_BOOT", str(R / "media/cdos86.img"))).read_bytes())
    run(
        d,
        "mformat",
        "-C",
        "-i",
        "fat.img",
        "-t",
        "40",
        "-h",
        "2",
        "-n",
        "8",
        "-c",
        "2",
        "::",
    )
    (d / "data").write_bytes(b"KEEP CONTENT\r\n\x1a")
    for name, attribute in [
        ("N.TXT", ""),
        ("H.TXT", "+h"),
        ("S.TXT", "+s"),
        ("SH.TXT", "+s +h"),
        ("RO.TXT", "+r"),
        ("HR.TXT", "+h +r"),
        ("Q.TXT", "+h"),
        ("W1.DAT", "+h"),
        ("W2.DAT", "+s"),
    ]:
        run(d, "mcopy", "-i", "fat.img", "data", "::" + name)
        if attribute:
            run(d, "mattrib", "-i", "fat.img", *attribute.split(), "::" + name)
    run(d, "mmd", "-i", "fat.img", "::SUB")
    run(d, "mlabel", "-i", "fat.img", "::KEEPVOL")
    return d


def session(d, cases):
    cfg = (
        (R / "media/cdos86.cfg")
        .read_text()
        .replace('driver = "sdl"', 'driver = "null"')
        .replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        .replace('file     = "cdostools.img"', 'file     = "fat.img"')
    )
    cfg = re.sub(
        r'(?m)^path\s*=\s*"([^"\n]+)"',
        lambda m: 'path = "' + str((R / "media" / m[1]).resolve()) + '"',
        cfg,
    )
    (d / "cfg").write_text(cfg)
    keys = {
        " ": "Space",
        "\r": "Return",
        "\x04": "+Ctrl d -Ctrl",
        ":": "+Shift Semicolon -Shift",
        ".": "Period",
        "[": "LeftBracket",
        "]": "RightBracket",
        "=": "Equal",
        "*": "+Shift 8 -Shift",
        ",": "Comma",
        "-": "Minus",
        "/": "Slash",
        "\\": "Backslash",
    }
    commands = ["c f000000"]

    def text(value):
        for ch in value:
            commands.extend(["key " + keys.get(ch, ch), "c 200000"])

    for command, label, answer in cases:
        text("cls")
        commands.extend(["key Return", "c 2000000"])
        text(command)
        commands.extend(["key Return", "c 4000000"])
        if answer:
            text(answer)
            commands.append("c 4000000")
        commands.append(f'save "{label}.bin" bin b800:0000 fa0')
    commands.append("q")
    with (d / "pce.log").open("wb") as log:
        subprocess.run(
            ["pce-ibmpc", "-c", "cfg", "-t", "null", "-g", "vga"],
            cwd=d,
            input=("\n".join(commands) + "\n").encode(),
            stdout=log,
            stderr=log,
            check=True,
            timeout=180,
        )
    screens = {}
    for _, label, _ in cases:
        b = (d / (label + ".bin")).read_bytes()
        screens[label] = "\n".join(
            b[o : o + 160 : 2].decode("ascii", "replace").rstrip()
            for o in range(0, 3840, 160)
        )
        (d / (label + ".txt")).write_text(screens[label])
    return screens


def deletion():
    d = fixture("cdos-hidden-delete-")
    before = entries(d / "fat.img")
    cases = [
        ("era b:h.txt", "hidden", ""),
        ("era b:s.txt", "system", ""),
        ("era b:sh.txt", "both", ""),
        ("era b:*.dat", "wild", ""),
        ("era b:hr.txt", "readonly", ""),
        ("eraq b:q.txt", "query", "y"),
        ("ren b:new.txt=b:n.txt", "rename", ""),
    ]
    screens = session(d, cases)
    after = entries(d / "fat.img")
    for name in [
        b"H       TXT",
        b"S       TXT",
        b"SH      TXT",
        b"W1      DAT",
        b"W2      DAT",
        b"Q       TXT",
    ]:
        assert name not in after, (name, screens)
    for name in [b"RO      TXT", b"HR      TXT", b"KEEPVOL    ", b"SUB        "]:
        assert after[name] == before[name], (name, after.get(name), before[name])
    assert b"N       TXT" not in after and b"NEW     TXT" in after, after
    assert run(d, "mtype", "-i", "fat.img", "::NEW.TXT") == b"KEEP CONTENT\r\n\x1a"
    print(
        "PASS: ERA/ERAQ exact/wildcard HIDDEN/SYSTEM deletion, RO protection, label/directory preservation and rename",
        flush=True,
    )


def listings():
    d = fixture("cdos-hidden-list-")
    cases = [("sdir b:*.txt", "normal", ""),
             ("sdir b:*.txt [sys]", "system", ""),
             ("sdir b:*.txt [dir sys]", "all", ""),
             ("sdir b:*.txt [sys short]", "short", ""),
             ("sdir b:*.txt [sys size]", "size", ""),
             ("dir.cmd b:*.txt [s]", "external-dir", ""),
             ("dir b:*.txt [s]", "internal-dir", "")]
    screens = session(d,cases)
    for label in ["normal","system","all","short","size","external-dir","internal-dir"]:
        body = screens[label].split("\n",1)[-1]
        names = set(re.findall(r"(?m)(?:^|[ :])([A-Z]+)\s+[.]?TXT\b",body))
        wanted = {"N","RO"} if label=="normal" else {"H","S","SH","HR","Q"}
        if label=="all": wanted |= {"N","RO"}
        assert names==wanted,(label,names,wanted,body)
    for text in ["Hid","Sys","S+H"]: assert text in screens["system"],screens["system"]
    print("PASS: shared SDIR normal/SYS/all/SHORT/SIZE and internal/external DIR filtering and HIDDEN indicators",flush=True)


def cpm_listing():
    d=fixture("cdos-hidden-cpm-")
    cases=[("sdir a:batch.cmd", "normal", ""),
           ("sdir a:batch.cmd [sys]", "sys", ""),
           ("sdir a:batch.cmd [dir sys]", "all", ""),
           ("dir.cmd a:batch.cmd [s]", "dir-sys", "")]
    screens=session(d,cases)
    assert not re.search(r"(?m)^BATCH[ .]",screens["normal"]),screens["normal"]
    for label in ["sys","all"]:
        assert re.search(r"(?m)^BATCH[ .].*Sys",screens[label]),screens[label]
        assert "Hid" not in screens[label] and "S+H" not in screens[label],screens[label]
    assert re.search(r"BATCH\s+CMD",screens["dir-sys"]),screens["dir-sys"]
    print("PASS: CP/M normal-only default, explicit SYS/all selection and shared DIR [S]; no false HIDDEN flags",flush=True)


def ls_rm():
    """Exercise real utilities, including deletion policy, on disposable FAT."""
    d=fixture("cdos-hidden-ls-rm-")
    for tool in ["ls", "rm"]:
        run(d,"mcopy","-i","fat.img",str(R.parent/"cpm86-hacking"/(tool+".cmd")),"::"+tool+".cmd")
    before=entries(d/"fat.img")
    cases=[("b:ls -b b:*.txt","normal",""),
           ("b:ls -ab b:*.txt","all",""),
           ("b:ls -al b:*.txt","long",""),
           ("b:rm b:*.txt","rm-normal",""),
           ("b:ls -ab b:*.txt","after-normal",""),
           ("b:rm -a b:*.txt","rm-all",""),
           ("b:ls -ab b:*.txt","after-all",""),
           ("b:rm -af b:*.txt","rm-force",""),
           ("b:ls -al b:*.*","final","")]
    screens=session(d,cases)
    def names(label):
        return set(re.findall(r"(?mi)^([a-z]+)\.txt$",screens[label]))
    assert names("normal")=={"N","RO"},screens["normal"]
    assert names("all")=={"N","H","S","SH","RO","HR","Q"},screens["all"]
    assert names("after-normal")=={"H","S","SH","RO","HR","Q"},screens["after-normal"]
    assert names("after-all")=={"RO","HR"},screens["after-all"]
    for flags,name in [("--H-","H"),("-S--","S"),("-SH-","SH"),("--HR","HR")]:
        assert re.search(re.escape(flags)+r" +"+name+r" +[.]TXT",screens["long"]),screens["long"]
    after=entries(d/"fat.img")
    assert not any(n[8:]==b"TXT" for n in after),after
    for name in [b"SUB        ",b"KEEPVOL    "]:
        assert after[name]==before[name],(name,after[name],before[name])
    assert "D---" in screens["final"],screens["final"]
    print("PASS: LS normal/all/HIDDEN flags; RM default/-a/-af, RO protection, directory and label preservation",flush=True)


def classic(boot):
    """Check LS/RM on an explicitly supplied original boot disk copy."""
    h=sys.modules[__name__]
    boot=Path(boot);d=Path(tempfile.mkdtemp(prefix='hidden-classic-'));print(d,flush=True)
    (d/'cdos86.img').write_bytes(boot.read_bytes())
    (d/'diskdefs').write_bytes((h.R/'media/diskdefs').read_bytes())
    h.run(d,'python3',str(h.R/'tools/cpm86twist.py'),'untwist',str(h.R/'media/base.img'),'data.img')
    (d/'data.img').write_bytes((d/'data.img').read_bytes().ljust(327680,b'\xe5'))
    for tool in ['ls','rm']:h.run(d,'cpmcp','-f','cpm86-320','data.img',str(h.R.parent/'cpm86-hacking'/(tool+'.cmd')),'0:')
    (d/'text').write_bytes(b'unchanged\r\n\x1a')
    for n in ['NORMAL.TXT','SYSTEM.TXT','READONLY.TXT']:h.run(d,'cpmcp','-f','cpm86-320','data.img','text','0:'+n)
    b=bytearray((d/'data.img').read_bytes())
    for o in range(4096,4096+64*32,32):
     if b[o+1:o+12]==b'SYSTEM  TXT':b[o+10]|=128
     if b[o+1:o+12]==b'READONLYTXT':b[o+9]|=128
    (d/'data.img').write_bytes(b)
    h.run(d,'python3',str(h.R/'tools/cpm86twist.py'),'twist','data.img','fat.img')
    screens=h.session(d,[('b:ls -al b:*.txt','all',''),('b:rm b:*.txt','normal',''),('b:ls -ab b:*.txt','remaining',''),('b:rm -af b:*.txt','force','')])
    assert '-S-- SYSTEM' in screens['all'],screens
    assert '---R READONLY' in screens['all'],screens
    assert '--H' not in screens['all'],screens
    remaining=screens['remaining'].rsplit('b:ls -ab b:*.txt',1)[-1]
    assert 'NORMAL.TXT' not in remaining and 'SYSTEM.TXT' in remaining and 'READONLY.TXT' in remaining,screens
    h.run(d,'python3',str(h.R/'tools/cpm86twist.py'),'untwist','fat.img','after.img')
    listing=h.run(d,'cpmls','-f','cpm86-320','after.img').decode()
    assert '.txt' not in listing.lower(),listing
    print('PASS: classic LS/RM SYSTEM/RO/default/-af compatibility: '+str(boot),flush=True)

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "delete":
        deletion()
    elif sys.argv[1] == "cpm":
        cpm_listing()
    elif sys.argv[1] == "list": listings()
    elif sys.argv[1] == "ls-rm": ls_rm()

    elif sys.argv[1] == "classic": classic(sys.argv[2])
