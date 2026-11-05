"""Differential geometry test against the original 8032h..813Bh machine code.

This tiny interpreter accepts only the instructions in that straight-line
calculation. Unknown opcodes fail; no host copy of the geometry formula is used.
"""
from pathlib import Path
import ctypes,subprocess,tempfile,itertools
root=Path(__file__).resolve().parents[1]
b=(root/'../../extra/fm.cmd').read_bytes();code=b[128:58304];data=b[58304:73808]
class Config(ctypes.Structure):_fields_=[('value',ctypes.c_ubyte*16)]
class Rect(ctypes.Structure):_fields_=[(n,ctypes.c_int) for n in ('row','column','width','height')]
class Layout(ctypes.Structure):_fields_=[(n,Rect) for n in ('files','menu','prompt')]
def original(cfg,rows,cols,wide=0):
    mem=bytearray(data);mem[0xcea]=rows;mem[0xceb]=cols
    for i,a in enumerate([0xcfc,0xcfe,0xd0e,0xd10,0xd12,0xd14,0xd16,0xd18,0xd02,0xd04,0xd06,0xd08,0xd0a,0xd0c,0x106a,0x106c]):mem[a]=cfg.value[i]
    mem[0xd00]=wide
    pc=[0x8032,0x813f,0x825c,0x8373,0x846c][cfg.value[1]-1];ax=bx=0;stack=[];zero=False
    while pc not in (0x813c,0x8259,0x8370,0x8469,0x8564):
        op=code[pc];pc+=1
        if op in (0xa0,0xa2):
            addr=int.from_bytes(code[pc:pc+2],'little');pc+=2
            if op==0xa0:ax=(ax&0xff00)|mem[addr]
            else:mem[addr]=ax&255
        elif op==0x32:
            assert code[pc]==0xe4;pc+=1;ax&=255
        elif op==0x93:ax,bx=bx,ax
        elif op==0x50:stack.append(ax)
        elif op==0x58:ax=stack.pop()
        elif op==0x40:ax=(ax+1)&65535
        elif op==0x48:ax=(ax-1)&65535
        elif op in (0x2b,0x03):
            assert code[pc]==0xc3;pc+=1
            ax=(ax-bx if op==0x2b else ax+bx)&65535
        elif op==0xa1:
            addr=int.from_bytes(code[pc:pc+2],'little');pc+=2;ax=int.from_bytes(mem[addr:addr+2],'little')
        elif op==0x0b:
            assert code[pc]==0xc0;pc+=1;zero=ax==0
        elif op in (0x74,0xeb):
            displacement=int.from_bytes(code[pc:pc+1],'little',signed=True);pc+=1
            if op==0xeb or zero:pc+=displacement
        elif op==0xb8:ax=int.from_bytes(code[pc:pc+2],'little');pc+=2
        elif op==0xc6:
            assert code[pc]==6;pc+=1
            addr=int.from_bytes(code[pc:pc+2],'little');pc+=2
            mem[addr]=code[pc];pc+=1
        elif op==0xc7:
            assert code[pc]==6;pc+=1
            addr=int.from_bytes(code[pc:pc+2],'little');pc+=2
            mem[addr:addr+2]=code[pc:pc+2];pc+=2
        else:raise AssertionError('Unexpected opcode %02x at %04x'%(op,pc-1))
    assert not stack
    return [tuple(mem[a:a+4]) for a in (0xdd0,0xe62,0xd96)]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'layout.so'
    subprocess.run(['cc','-shared','-fPIC','-Wno-deprecated-non-prototype',str(root/'layout.c'),'-o',str(lib)],check=True)
    f=ctypes.CDLL(str(lib)).fm_layout_calculate
    f.argtypes=[ctypes.POINTER(Layout),ctypes.POINTER(Config),ctypes.c_int,ctypes.c_int,ctypes.c_int]
    count=0
    for rows,cols,size,prompt,margin,position,wide in itertools.product([24,25,43],[80,100],[8,17],[1,2],[0,2],range(1,6),[0,1]):
        c=Config();c.value[1]=position;c.value[8]=size;c.value[9]=prompt
        for i in range(10,14):c.value[i]=margin
        out=Layout();assert f(ctypes.byref(out),ctypes.byref(c),rows,cols,wide)
        got=[tuple(getattr(rec,k) for k in ('row','column','width','height')) for rec in (out.files,out.menu,out.prompt)]
        assert got==original(c,rows,cols,wide),(got,original(c,rows,cols,wide))
        count+=1
    assert not f(ctypes.byref(out),ctypes.byref(c),2,2,0)
print('PASS: %d layouts match original machine-code calculation; invalid geometry rejected'%count)
