"""Compare all 256 keys against original normalization machine code."""
from pathlib import Path
import ctypes,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
code=(root/'../../extra/fm.cmd').read_bytes()[128:58304]
def original(key):
    pc=0x68c8;ax=key;saved=key;zero=False
    for step in range(100):
        op=code[pc];pc+=1
        if op==0x32:assert code[pc]==0xe4;pc+=1;ax&=255
        elif op==0x3c:zero=(ax&255)==code[pc];pc+=1
        elif op in (0x74,0x75,0xeb):
            delta=int.from_bytes(code[pc:pc+1],'little',signed=True);pc+=1
            if op==0xeb or (zero if op==0x74 else not zero):pc+=delta
        elif op==0xe9:delta=int.from_bytes(code[pc:pc+2],'little',signed=True);pc+=2;pc+=delta
        elif op==0xb8:ax=int.from_bytes(code[pc:pc+2],'little');pc+=2
        elif op==0xa0:assert code[pc:pc+2]==bytes.fromhex('921c');pc+=2;ax=(ax&0xff00)|saved
        elif op==0x8a:assert code[pc:pc+3]==bytes.fromhex('06921c');pc+=3;ax=(ax&0xff00)|saved
        elif op==0xc6:assert code[pc:pc+3]==bytes.fromhex('06921c');pc+=3;saved=code[pc];pc+=1
        elif op==0xc3:return ax
        else:raise AssertionError('Unknown opcode %02x at %04x'%(op,pc-1))
    raise AssertionError('Unterminated original key routine')
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'keys.so'
    subprocess.run(['cc','-shared','-fPIC','-Wno-deprecated-non-prototype',str(root/'keys.c'),'-o',str(lib)],check=True)
    dll=ctypes.CDLL(str(lib))
    for k in range(256):assert dll.fm_key_normalize(k)==original(k),k
    t=dll.fm_key_translate;t.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int]
    assert t(65,b'AB',b'BC',2)==67
    assert t(65,b'AB',b'BC',1)==66
    assert t(65,b'\0A',b'BC',2)==65
    assert t(65,b'AA',b'BC',2)==66
    assert t(255,b'\xff',b'\xc8',1)==200
    assert t(65,None,None,0)==65
print('PASS: all 256 keys match original machine code; terminal-map cascades and bounds checked')
