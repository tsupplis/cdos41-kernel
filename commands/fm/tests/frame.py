"""Check border cells and colour mappings against the release DATA tables."""
from pathlib import Path
import ctypes,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
d=(root/'../../extra/fm.cmd').read_bytes()[58304:]
class Rect(ctypes.Structure):_fields_=[(k,ctypes.c_int) for k in ('row','column','width','height')]
Cell=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int)
class Canvas(ctypes.Structure):_fields_=[('rows',ctypes.c_int),('columns',ctypes.c_int),('cell',Cell)]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'frame.so'
    subprocess.run(['cc','-shared','-fPIC','-Wno-deprecated-non-prototype',str(root/'frame.c'),'-o',str(lib)],check=True)
    dll=ctypes.CDLL(str(lib));frame=dll.fm_frame;frame.argtypes=[ctypes.POINTER(Canvas),ctypes.POINTER(Rect),ctypes.c_int,ctypes.c_int]
    for fg in range(16):
        for bg in range(16):
            for rev in range(2):
                a,b=d[0x9e2+fg],d[0x9e2+bg]
                if rev:a,b=b,a
                assert dll.fm_attribute(fg,bg,rev)==((b<<4)|a)&127
    calls={}
    @Cell
    def cell(row,column,char,attr):
        assert (row,column) not in calls
        calls[row,column]=(char,attr);return 1
    canvas=Canvas(24,80,cell)
    for graphics in (0,1):
        base=0x9f2 if graphics else 0xa0e
        g=[d[base+i] for i in d[0xdce+33:0xdce+40]]
        for w,h in [(2,2),(20,21),(60,21)]:
            calls.clear();rect=Rect(1,1,w,h)
            assert frame(ctypes.byref(canvas),ctypes.byref(rect),graphics,0x50)
            expected={(1,1):g[0],(1,w):g[1],(h,1):g[2],(h,w):g[3]}
            for x in range(2,w):expected[1,x]=g[4];expected[h,x]=g[4]
            for y in range(2,h):expected[y,1]=g[5];expected[y,w]=g[6]
            assert calls=={p:(v,0x50) for p,v in expected.items()}
    calls.clear();rect=Rect(23,79,2,2)
    assert not frame(ctypes.byref(canvas),ctypes.byref(rect),1,0) and not calls
print('PASS: 512 colour cases; six exact frame-cell comparisons; bounds rejection')
