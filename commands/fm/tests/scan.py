"""Exercise search results and cleanup through a deterministic BDOS adapter."""
from pathlib import Path
import ctypes as C
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
class File(C.Structure):
    _fields_ = [('name', C.c_char*13), ('raw', C.c_char*32), ('directory', C.c_int)]
Get = C.CFUNCTYPE(C.c_int)
Set = C.CFUNCTYPE(C.c_int, C.c_int)
Ptr = C.CFUNCTYPE(C.c_int, C.c_void_p)
class Ops(C.Structure):
    _fields_ = [('getuser', Get), ('setuser', Set), ('setdma', Ptr),
                ('first', Ptr), ('next', Ptr)]

def entry(name=b'FILE    TXT', user=4, flag=0):
    e = bytearray(32)
    e[0] = user
    e[1:12] = name
    e[16] = flag
    return bytes(e)

with tempfile.TemporaryDirectory() as tmp:
    lib = Path(tmp)/'scan.so'
    subprocess.run(['cc', '-std=c89', '-shared', '-fPIC',
                    '-Wno-deprecated-non-prototype', str(root/'scan.c'),
                    str(root/'dirlist.c'), '-o', str(lib)], check=True)
    scan = C.CDLL(str(lib)).fm_scan
    scan.argtypes = [C.POINTER(Ops), C.c_int, C.c_int, C.c_int,
                     C.POINTER(File), C.c_int, C.POINTER(C.c_int), C.c_void_p]
    def run(results, fat=0, capacity=8, drive=3, saved=7):
        restore = C.create_string_buffer(128)
        state = {'user': saved, 'dma': C.addressof(restore), 'index': 0}
        calls, fcbs = [], []
        @Get
        def getuser():
            calls.append(('getuser',))
            return state['user']
        @Set
        def setuser(user):
            calls.append(('user', user)); state['user'] = user
            return 0
        @Ptr
        def setdma(address):
            calls.append(('dma', address)); state['dma'] = address
            return 0
        def search(address, first):
            fcbs.append(C.string_at(address,36))
            calls.append(('first' if first else 'next',))
            i = state['index']; state['index'] += 1
            if i == len(results): return 255
            slot, raw = results[i]
            if 0 <= slot <= 3:
                C.memset(state['dma'], 229, 128)
                C.memmove(state['dma']+slot*32, raw, 32)
            # Exercise reinstatement of the drive flag, like the original.
            C.c_ubyte.from_address(address).value = 0
            return slot
        first = Ptr(lambda a: search(a, True))
        next_ = Ptr(lambda a: search(a, False))
        ops = Ops(getuser, setuser, setdma, first, next_)
        files = (File*8)(); count = C.c_int(99)
        result = scan(C.byref(ops), drive, 4, fat, files, capacity,
                      C.byref(count), C.addressof(restore))
        assert state['user'] == saved and state['dma'] == C.addressof(restore)
        for fcb in fcbs:
            assert fcb[0] == (drive|128) and fcb[1:12] == b'?'*11
            assert fcb[12:] == bytes(24)
        if fcbs:
            assert calls[-2:] == [('dma',C.addressof(restore)),('user',saved)]
        return result, count.value, files, calls
    records = [(0,entry()), (1,entry(user=5)), (2,entry(b'SUBDIR     ',flag=64)),
               (3,entry(b'LAST    CMD'))]
    status, count, files, _ = run(records, fat=1)
    assert (status,count)==(1,3)
    assert [files[i].name for i in range(count)] == [b'FILE.TXT    ',b'SUBDIR      ',b'LAST.CMD    ']
    assert [files[i].directory for i in range(count)] == [0,1,0]
    assert C.string_at(C.addressof(files[1])+File.raw.offset,32) == records[2][1]
    status,count,files,_ = run(records, fat=0)
    assert (status,count)==(1,3) and not any(files[i].directory for i in range(count))
    assert run([])[:2] == (1,0)
    assert run(records,capacity=2)[:2] == (0,2)
    assert run([(0,entry()),(1,entry())],capacity=2)[:2] == (1,2)
    assert run([(0,entry()),(4,bytes(32))])[:2] == (-1,1)
    status,count,files,calls = run([],drive=0)
    assert status == -1 and count == 99 and not calls
    status,count,files,calls = run([],saved=32)
    assert status == -1 and calls == [('getuser',)]
print('PASS: search slots, FAT/CPM distinction, user filtering, empty/full/truncated/error cleanup and FCB restoration')
