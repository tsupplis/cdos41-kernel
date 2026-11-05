"""Boundary cases from the original branches, plus navigation invariants."""
from pathlib import Path
import ctypes as C,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
class Nav(C.Structure):_fields_=[(k,C.c_int) for k in ('count','selected','offset','capacity','columns')]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'nav.so';subprocess.run(['cc','-shared','-fPIC','-Wno-deprecated-non-prototype',str(root/'navigate.c'),'-o',str(lib)],check=True)
    f=C.CDLL(str(lib)).fm_navigate;f.argtypes=[C.POINTER(Nav),C.c_int]
    cases=[((10,10,6,6,3),12,(1,0)),((10,1,0,6,3),8,(10,6)),
           ((10,2,0,6,3),11,(2,0)),((10,4,0,6,3),11,(1,0)),
           ((10,6,0,6,3),10,(9,3)),((8,6,0,6,3),10,(6,3)),
           ((10,10,6,6,3),10,(10,6)),((10,7,3,6,3),1,(1,0)),
           ((10,1,0,6,3),26,(10,6)),((0,0,0,6,3),10,(0,0))]
    for before,key,after in cases:
        n=Nav(*before);assert f(C.byref(n),key)>=0
        assert (n.selected,n.offset)==after,(before,key,n.selected,n.offset)
    count=0
    for total in range(1,101):
        for cols in (1,2,3,5):
            cap=cols*4
            for selected in range(1,total+1):
                offset=max(0,((selected-1)//cols)*cols-cap+cols)
                for key in (1,26,8,10,11,12):
                    n=Nav(total,selected,offset,cap,cols)
                    assert f(C.byref(n),key)>=0
                    assert 1<=n.selected<=total and 0<=n.offset<n.selected
                    assert n.selected-n.offset<=cap and n.offset%cols==0
                    count+=1
    n=Nav(10,1,0,0,0);assert f(C.byref(n),12)==-1
print('PASS: 10 reference-derived boundary cases and %d navigation invariants'%count)
