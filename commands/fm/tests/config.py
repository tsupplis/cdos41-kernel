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

    class Reader(ctypes.Structure):
        _fields_=[('line',ctypes.c_char*82),('used',ctypes.c_int),
                  ('overflow',ctypes.c_int),('ended',ctypes.c_int),('assignments',ctypes.c_int)]
    b=(ROOT/'../../extra/fm.cmd').read_bytes()
    d=b[128+int.from_bytes(b[1:3],'little')*16:]
    offsets=[0xcfc,0xcfe,0xd0e,0xd10,0xd12,0xd14,0xd16,0xd18,
             0xd02,0xd04,0xd06,0xd08,0xd0a,0xd0c,0x106a,0x106c]
    expected=[d[x] for x in offsets]
    for i,v in {2:0,3:5,4:0,5:4,6:15,7:1,8:17,11:2}.items():expected[i]=v
    native.fm_config_defaults(ctypes.byref(cfg))
    assert list(cfg.value)==expected
    def parse(data):
        native.fm_config_defaults(ctypes.byref(cfg));reader=Reader()
        native.fm_config_begin(ctypes.byref(reader))
        for ch in data:native.fm_config_feed(ctypes.byref(cfg),ctypes.byref(reader),ch)
        native.fm_config_finish(ctypes.byref(cfg),ctypes.byref(reader))
        return reader.assignments
    assert parse((ROOT/'../../extra/fm.cfg').read_bytes())==8
    assert list(cfg.value)==expected
    assert parse(b'object fg color=7\r\nCOMMAND BG COLOR=2\nKEY FG COLOR=9')==3
    assert (cfg.value[2],cfg.value[5],cfg.value[14])==(7,2,9)
    assert parse(b'OBJECT FG COLOR=3\x1aOBJECT FG COLOR=6')==1 and cfg.value[2]==3
    assert parse(b'x'*82+b'\nOBJECT FG COLOR=4\r')==1 and cfg.value[2]==4
    assert parse(b'OBJECT FG COLOR='+b'1'*90+b'\n')==0
    assert parse(b' OBJECT FG COLOR=4\nOBJECT FG COLOR=bad\n')==0
    print('PASS: reference defaults, streamed FM.CFG, CR/LF, EOF, Ctrl-Z and oversized lines')
