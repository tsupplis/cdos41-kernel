"""Check the supplied configuration against the portable C assignment parser."""
from pathlib import Path
import ctypes, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
class Config(ctypes.Structure):
    _fields_=[('value',ctypes.c_ubyte*16)]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'config.so'
    subprocess.run(['cc','-shared','-fPIC','-std=c89','-Wno-deprecated-non-prototype',str(ROOT/'config.c'),'-o',str(lib)],check=True)
    native=ctypes.CDLL(str(lib)); call=native.fm_config_assignment
    call.argtypes=[ctypes.POINTER(Config),ctypes.POINTER(ctypes.c_char_p)]
    cfg=Config();found=[]
    for line in (ROOT/'../../extra/fm.cfg').read_bytes().split(b'\x1a')[0].splitlines():
        ptr=ctypes.c_char_p(line)
        result=call(ctypes.byref(cfg),ctypes.byref(ptr))
        if result: found.append(result)
    assert found==[16,17,18,19,20,21,28,29],found
    assert list(cfg.value[2:8])==[0,5,0,4,15,1]
    assert list(cfg.value[14:])==[14,1]
    print('PASS: all eight assignments in the unmodified release FM.CFG')
