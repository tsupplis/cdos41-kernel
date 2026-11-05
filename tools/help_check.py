#!/usr/bin/env python3
"""Validate maintained help against packaged commands, excluding extras."""

from pathlib import Path
import re

R = Path(__file__).resolve().parent.parent
s = (R / "commands/helphlp/help.dat").read_text()
topics = {
    m.upper().strip().split(" (")[0] for m in re.findall(r"(?m)^\s*///1([^\r\n]+)", s)
}
removed = {
    "ABORT",
    "CONFIG",
    "DOS8087",
    "DOSMEM",
    "DOSUSPND",
    "SETDEF",
    "VCMODE",
    "BUFFERED",
    "DYNAMIC",
    "CARDFILE",
    "DRTALK",
    "DISKSTAT",
    "NEAT",
    "CTTY",
    "VERIFY",
    "FORMAT",
    "FDISK",
}
assert not topics & removed, topics & removed
media = (R / "media/Makefile").read_text()
files = re.findall(r"\.\./(?:commands|base)/[^\s\\]+\.(?:cmd|exe|com)", media, re.I)
commands = {Path(f).stem.upper() for f in files}
commands.discard("PIP4")
commands.add("PIP")
builtins = {
    "CLS",
    "DIR",
    "USER",
    "ORDER",
    "COMSIZE",
    "ADDMEM",
    "8087",
    "SUSPEND",
    "PRINTER",
    "PAUSE",
    "REM",
    "SYS",
    "RUNMENU",
    "STOP",
    "CD",
    "MD",
    "RD",
    "DEL",
    "DELQ",
    "RENAME",
}
assert commands | builtins <= topics, sorted((commands | builtins) - topics)
for name in ["HELP.EDX", "LSN.EDX"]:
    assert (R / "commands/dredix" / name.lower()).is_file()
    assert "../commands/dredix/" + name.lower() in media
assert not (R / "base/letter.txt").exists()
assert "../base/letter.txt" not in media
assert "../base/help.hlp" not in media, "Distributions must use the rebuilt help index"
b = (R / "commands/helphlp/help.hlp").read_bytes()
roots = set()
indexed = 0
# HELP reads records until the '$' sentinel; the index is not fixed at 2 KB.
# LANGUAGES pushes the maintained database beyond the former 128-entry bound.
entries = []
for a in range(0, len(b), 16):
    e = b[a : a + 16]
    assert len(e) == 16, "Truncated HELP index"
    if e[0] == ord('$'):
        index_end = ((a + 16 + 127) // 128) * 128
        break
    assert 1 <= e[15] <= 9, (a, e)
    entries.append(e)
else:
    raise AssertionError("Missing HELP index terminator")
for e in entries:
    name = e[:12].decode("ascii").strip()
    p = int.from_bytes(e[12:14], "little") * 128 + e[14]
    assert index_end <= p < len(b), (name, p, len(b))
    indexed += 1
    if e[15] == 1:
        roots.add(name)
assert roots == {t[:12] for t in topics}, roots ^ topics
assert indexed == len(re.findall(r"(?m)^\s*///[1-9]", s)), indexed
for text in [
    b"Ctrl-Alt-Esc",
    b"Press any key to continue...",
    b"no separate DIR",
    b"DEL -> ERA.CMD",
]:
    assert text in b, text
print(
    f"PASS: {len(topics)} help topics, {indexed} index entries, packaged commands/built-ins/aliases, editor assets and cleaned media"
)
