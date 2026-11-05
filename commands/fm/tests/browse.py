"""Integration checks: sorted names, translated keys, viewport and cell output."""
from pathlib import Path
import ctypes as C
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
class Rect(C.Structure):
    _fields_=[(n,C.c_int) for n in ('row','column','width','height')]
class Nav(C.Structure):
    _fields_=[(n,C.c_int) for n in ('count','selected','offset','capacity','columns')]
class Browser(C.Structure):
    _fields_=[('navigation',Nav),('area',Rect),('names',C.POINTER(C.c_char_p)),
              ('stride',C.c_int),('normal',C.c_int),('selected',C.c_int)]
Cell=C.CFUNCTYPE(C.c_int,C.c_int,C.c_int,C.c_int,C.c_int)
class Canvas(C.Structure):
    _fields_=[('rows',C.c_int),('columns',C.c_int),('cell',Cell)]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'browse.so'
    subprocess.run(['cc','-std=c89','-shared','-fPIC','-Wno-deprecated-non-prototype',
        *[str(root/f) for f in ('browse.c','navigate.c','keys.c','frame.c','dirlist.c','event.c','conio.c')],
        '-o',str(lib)],check=True)
    dll=C.CDLL(str(lib));view=Browser();area=Rect(2,3,30,5)
    names=(C.c_char_p*8)(*[('F%07d.CMD'%i).encode() for i in range(7,-1,-1)])
    assert dll.fm_directory_sort(names,8)
    assert dll.fm_browser_open(C.byref(view),names,8,C.byref(area),14,7,112)
    pixels={};writes=[]
    @Cell
    def cell(y,x,ch,attr):
        assert 2<=y<7 and 3<=x<33
        pixels[y,x]=(ch,attr);writes.append((y,x));return 1
    canvas=Canvas(24,80,cell)
    def draw():
        pixels.clear();writes.clear()
        assert dll.fm_browser_draw(C.byref(view),C.byref(canvas))
        selected=[p for p,(ch,a) in pixels.items() if a==112]
        assert len(selected)==12
        n=view.navigation
        relative=n.selected-1-n.offset
        row=3+relative//2;col=4+(relative%2)*14
        assert selected==[(row,col+j) for j in range(12)]
        assert bytes(pixels[row,col+j][0] for j in range(12))==names[n.selected-1]
        assert pixels[2,3][0]==218 and pixels[6,32][0]==217
    draw()
    for raw_key in (0xcd,0xd0,0xd0,0xd0,0xcb,0xc8,0xcf,0xc7):
        assert dll.fm_browser_key(C.byref(view),raw_key)>=0
        draw()
    assert view.navigation.selected==1
    assert dll.fm_browser_key(C.byref(view),27)==0
    # Short final page must erase stale content before repainting.
    assert dll.fm_browser_open(C.byref(view),names,1,C.byref(area),14,7,112)
    draw()
    assert all(pixels[5,x]==(32,7) for x in range(4,32))
    assert dll.fm_browser_open(C.byref(view),None,0,C.byref(area),14,7,112)
    pixels.clear()
    assert dll.fm_browser_draw(C.byref(view),C.byref(canvas))
    assert not any(a==112 for ch,a in pixels.values())
    assert dll.fm_browser_key(C.byref(view),0xcd)==0
    writes.clear();small=Canvas(4,8,cell)
    assert not dll.fm_browser_draw(C.byref(view),C.byref(small)) and not writes
    @Cell
    def failed(y,x,ch,attr):return 0
    broken=Canvas(24,80,failed)
    assert not dll.fm_browser_draw(C.byref(view),C.byref(broken))
    # Drive the same pane through the console event pump.
    NoArg=C.CFUNCTYPE(C.c_int)
    Put=C.CFUNCTYPE(C.c_int,C.c_int)
    class Console(C.Structure):
        _fields_=[('acquire',NoArg),('release',NoArg),('put',Put),('read',NoArg),('held',C.c_int)]
    order=[];pending=[0xcd,-1,27]
    @NoArg
    def acquire():order.append('acquire');return 1
    @NoArg
    def release():order.append('release');return 1
    @NoArg
    def read():order.append('read');return pending.pop(0)
    @Put
    def put(c):return 1
    console=Console(acquire,release,put,read,0)
    assert dll.fm_browser_open(C.byref(view),names,8,C.byref(area),14,7,112)
    assert dll.fm_browser_paint(C.byref(view),C.byref(canvas),C.byref(console))
    assert order==['acquire','release'] and not console.held
    order.clear()
    args=(C.byref(view),C.byref(canvas),C.byref(console),None,None,0)
    assert dll.fm_browser_step(*args)==1 and view.navigation.selected==2
    assert order==['read','acquire','release'] and not console.held
    order.clear()
    assert dll.fm_browser_step(*args)==0 and order==['read']
    order.clear()
    assert dll.fm_browser_step(*args)==2 and order==['read'] and not console.held
    pending.append(0xcd);order.clear()
    assert dll.fm_browser_step(C.byref(view),C.byref(broken),C.byref(console),None,None,0)==-1
    assert order==['read','acquire','release'] and not console.held
print('PASS: browser sorting/key/scroll/render integration, selection highlight, empty/short repaint and output failure')
