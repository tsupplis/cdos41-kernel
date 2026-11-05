#!/usr/bin/env python3
"""Assemble core/console/devices and link the single-segment XIOS component."""

from pathlib import Path
import argparse, json, re, shutil, subprocess, os, tempfile

ROOT = Path(__file__).resolve().parent.parent
CON = ROOT / "kernel/con"
SOURCE = CON / "xios"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("variant", choices=("xios",))
args = parser.parse_args()
work = CON / ".xios" / args.variant
work.mkdir(parents=True, exist_ok=True)
for source in SOURCE.iterdir():
    if source.suffix in (".a86", ".inc", ".lib"):
        shutil.copyfile(source, work / source.name)
policy = (CON / "consoles.def").read_text()
for name in ("num_vir_cons", "num_serial_cons", "num_sys_cons"):
    policy = re.sub(r"\b" + name + r"\b", name.replace("_", ""), policy, flags=re.I)
(work / "consoles.inc").write_bytes(policy.replace("\n", "\r\n").encode("ascii"))


def run(command, log):
    result = subprocess.run(
        command, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    output = result.stdout.decode("latin1")
    (work / log).write_bytes(result.stdout)
    if result.returncode or re.search(
        r"ERROR NO:|SYNTAX ERROR|UNDEFINED|UNRESOLVED|NO FILE|OVERFLOW", output, re.I
    ):
        raise RuntimeError(output)
    return output


usage = {}
for name in ["core", "console", "devices"]:
    output = run(["pcdev_rasm86", name + ".a86", "$LO"], name + ".log")
    assert re.search(r"Number of errors:\s+0\.", output), output
    usage[name] = int(re.search(r"Use factor:\s*(\d+)%", output)[1])
run(
    [
        "pcdev_linkcmd",
        "linked.con=core,console,devices[cod[ori[0]],dat[ori[0],max[0]],locals,map,hard8087]",
    ],
    "link.log",
)
image = bytearray((work / "linked.con").read_bytes())
assert (
    image[0] == 1 and image[9] == 0 and image[127] == 0x20
), "Unexpected linked CMD format"
symbols = {
    name: int(value, 16)
    for value, name in re.findall(
        r"\b([0-9A-F]{4})\s+([A-Z][A-Z0-9]*)", (work / "linked.sym").read_text()
    )
}
for name, expected in json.loads((SOURCE / "abi.json").read_text()).items():
    assert symbols[name] == expected, (name, symbols.get(name), expected)
for offset, name in [(0xC00, "INIT"), (0xC03, "ENTRY")]:
    code = image[128:]
    assert code[offset] == 0xE9
    target = (
        offset
        + 3
        + int.from_bytes(code[offset + 1 : offset + 3], "little", signed=True)
    ) & 0xFFFF
    assert target == symbols[name], (name, target, symbols[name])
# UART input buffers reclaim only core startup code, never another module.
assert symbols["AUXBUFIN0"] == symbols["INIT"]
assert symbols["AUXBUFIN1"] == symbols["INIT"] + 1024
assert symbols["AUXTOPIN1"] == symbols["INIT"] + 2047
assert symbols["INITCODELEN"] >= 2048
# HARD8087 retains the explicit NDP instructions instead of linking an emulator.
# XIOS probes optional hardware itself; preserve its historical component flags.
image[127] = 0
for suffix, data in [
    ("sym", (work / "linked.sym").read_bytes()),
    ("map", (work / "linked.map").read_bytes()),
    ("con", image),
]:
    with tempfile.NamedTemporaryFile(dir=CON, delete=False) as output:
        output.write(data)
        temporary = output.name
    os.replace(
        temporary, CON / (("xios" if suffix == "con" else "squid") + "." + suffix)
    )
result = dict(
    variant=args.variant,
    use_factor=usage,
    file_bytes=len(image),
    loaded_bytes=int.from_bytes(image[1:3], "little") * 16,
)
(work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print("PASS: three-module XIOS:", json.dumps(result))
