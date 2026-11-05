"""Compare compiled C menu descriptors directly with original FM DATA records."""
from pathlib import Path
import ctypes,struct,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
b=(root/'../../extra/fm.cmd').read_bytes();start=128+int.from_bytes(b[1:3],'little')*16;d=b[start:]
def word(a):return struct.unpack_from('<H',d,a)[0]
def text(a):return d[a:d.index(0,a)] if a else b''
class Item(ctypes.Structure):
    _fields_=[('action',ctypes.c_char_p),('label',ctypes.c_char_p),('description',ctypes.c_char_p),('command',ctypes.c_char_p),('minimum',ctypes.c_int),('maximum',ctypes.c_int)]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'menu.so'
    subprocess.run(['cc','-shared','-fPIC',str(root/'menu.c'),'-o',str(lib)],check=True)
    module=ctypes.CDLL(str(lib));items=(Item*28).in_dll(module,'fm_menu_items')
    assert ctypes.c_int.in_dll(module,'fm_menu_count').value==28
    assert ctypes.c_int.in_dll(module,'fm_file_menu_count').value==17
    n=0
    for base,count in [(0x1c56,17),(0x1c78,11)]:
        for i in range(count):
            rec=word(base+2*i);item=items[n]
            assert item.label==text(word(rec+2)),n
            assert item.description==text(word(rec+10)),n
            assert item.command==text(word(rec+8)),n
            assert (item.minimum,item.maximum)==(word(rec+4),word(rec+6)),n
            n+=1
print('PASS: all 28 compiled menu records match the original labels, descriptions, commands and selection bounds')
