"""Console ownership ordering, failure cleanup and mapped input."""
from pathlib import Path
import ctypes as C
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
NoArg=C.CFUNCTYPE(C.c_int)
Put=C.CFUNCTYPE(C.c_int,C.c_int)
class Console(C.Structure):
    _fields_=[('acquire',NoArg),('release',NoArg),('put',Put),('read',NoArg),('held',C.c_int)]
with tempfile.TemporaryDirectory() as tmp:
    lib=Path(tmp)/'conio.so'
    subprocess.run(['cc','-std=c89','-shared','-fPIC','-Wno-deprecated-non-prototype',
        str(root/'conio.c'),str(root/'keys.c'),'-o',str(lib)],check=True)
    dll=C.CDLL(str(lib))
    write=dll.fm_console_write;write.argtypes=[C.POINTER(Console),C.c_char_p,C.c_int]
    key=dll.fm_console_key;key.argtypes=[C.POINTER(Console),C.c_char_p,C.c_char_p,C.c_int]
    events=[];state={'acquire':1,'release':1,'put':1,'key':-1}
    @NoArg
    def acquire():events.append('acquire');return state['acquire']
    @NoArg
    def release():events.append('release');return state['release']
    @Put
    def put(c):events.append(('put',c));return state['put']
    @NoArg
    def read():events.append('read');return state['key']
    con=Console(acquire,release,put,read,0)
    assert dll.fm_console_begin(C.byref(con))==1 and con.held==1
    assert dll.fm_console_begin(C.byref(con))==1 and events==['acquire']
    events.clear()
    assert write(C.byref(con),b'\x1bY !',4)==1
    assert events==['release',('put',27),('put',89),('put',32),('put',33),'acquire']
    assert con.held==1
    events.clear();state['put']=0
    assert write(C.byref(con),b'ab',2)==0
    assert events==['release',('put',97),'acquire'] and con.held==1
    events.clear();state['release']=0
    assert write(C.byref(con),b'ab',2)==0
    assert events==['release'] and con.held==1
    state['release']=1;state['put']=1;state['acquire']=0;events.clear()
    assert write(C.byref(con),b'a',1)==0 and con.held==0
    assert events==['release',('put',97),'acquire']
    state['acquire']=1;events.clear()
    assert write(C.byref(con),b'a',1)==1 and events==[('put',97)]
    events.clear()
    assert write(C.byref(con),None,0)==1 and not events
    assert write(C.byref(con),None,1)==0 and not events
    assert dll.fm_console_begin(C.byref(con))==1
    events.clear()
    assert key(C.byref(con),None,None,0)==-1
    assert events==['release','read'] and con.held==0
    state['key']=0
    assert key(C.byref(con),None,None,0)==0
    state['key']=65
    assert key(C.byref(con),b'A',b'\xc8',1)==11
    state['key']=256
    assert key(C.byref(con),None,None,0)==-2
    events.clear()
    assert key(C.byref(con),None,b'A',1)==-2 and not events
print('PASS: lock ordering, output failures, failed reacquisition, input release, NUL and mapped keys')
