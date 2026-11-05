"""Host rendering preview using the C geometry, border and colour modules."""
from pathlib import Path
import ctypes as C,subprocess,tempfile,html,json
root=Path(__file__).resolve().parents[1]
class Rect(C.Structure):_fields_=[(n,C.c_int) for n in ('row','column','width','height')]
class Layout(C.Structure):_fields_=[(n,Rect) for n in ('files','menu','prompt')]
class Config(C.Structure):_fields_=[('value',C.c_ubyte*16)]
Cell=C.CFUNCTYPE(C.c_int,C.c_int,C.c_int,C.c_int,C.c_int)
class Canvas(C.Structure):_fields_=[('rows',C.c_int),('columns',C.c_int),('cell',Cell)]
palette=['#000000','#0000aa','#00aa00','#00aaaa','#aa0000','#aa00aa','#aa5500','#aaaaaa','#555555','#5555ff','#55ff55','#55ffff','#ff5555','#ff55ff','#ffff55','#ffffff']
pixels=[[(32,7) for x in range(80)] for y in range(24)]
@Cell
def put(y,x,ch,attr):pixels[y][x]=(ch,attr);return 1
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'preview.so'
    subprocess.run(['cc','-shared','-fPIC','-Wno-deprecated-non-prototype',*[str(root/f) for f in ('layout.c','frame.c')],'-o',str(lib)],check=True)
    dll=C.CDLL(str(lib));cfg=Config();cfg.value[1]=1;cfg.value[8]=17;cfg.value[9]=1;cfg.value[11]=2
    layout=Layout();assert dll.fm_layout_calculate(C.byref(layout),C.byref(cfg),24,80,0)
    canvas=Canvas(24,80,put)
    for rect,fg,bg,border in [(layout.files,0,5,True),(layout.menu,0,4,True),(layout.prompt,15,1,False)]:
        attr=dll.fm_attribute(fg,bg,0)
        for y in range(rect.row,rect.row+rect.height):
            for x in range(rect.column,rect.column+rect.width):put(y,x,32,attr)
        if border:assert dll.fm_frame(C.byref(canvas),C.byref(rect),1,attr)
    for i,item in enumerate(json.loads((root/'menus.json').read_text())[:17]):
        y=layout.menu.row+1+i
        for j,ch in enumerate(item['label'][:layout.menu.width-2]):put(y,layout.menu.column+1+j,ord(ch),dll.fm_attribute(0,4,0))
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="480" viewBox="0 0 960 480">','<title>FM host rendering preview — no filesystem or keyboard backend</title>']
for y,row in enumerate(pixels):
    for x,(ch,attr) in enumerate(row):
        svg.append('<rect x="%d" y="%d" width="12" height="20" fill="%s"/>'%(x*12,y*20,palette[(attr>>4)&7]))
        if ch!=32:svg.append('<text x="%d" y="%d" fill="%s" font-family="monospace" font-size="20">%s</text>'%(x*12,y*20+16,palette[attr&15],html.escape(bytes([ch]).decode('cp437'))))
svg.append('</svg>');(root/'preview.svg').write_text('\n'.join(svg)+'\n')
print('Created preview.svg (host rendering only)')
