"""Disposable FAT image fixtures shared by checker and safety tests."""
import struct

def fixture(bits=12,clusters=None,spc=1,root=32):
    clusters=clusters or (700 if bits==12 else 6000)
    limit=clusters+2
    fatsiz=((limit*bits+7)//8+511)//512
    base=1; data=base+2*fatsiz+(root+15)//16
    total=data+clusters*spc
    assert total<65536
    b=bytearray(total*512)
    struct.pack_into('<HBHBHHBHHH',b,11,512,spc,base,2,root,total,0xf8,fatsiz,17,4)
    b[510:512]=b'\x55\xaa'
    def fat(c,v,copy=None):
        for k in range(2) if copy is None else [copy]:
            off=(base+k*fatsiz)*512+(c*bits//8)
            old=int.from_bytes(b[off:off+2],'little')
            if bits==16:new=v
            elif c&1:new=(old&15)|(v<<4)
            else:new=(old&0xf000)|(v&4095)
            b[off:off+2]=new.to_bytes(2,'little')
    end=0xfff if bits==12 else 0xffff
    fat(0,0xff8 if bits==12 else 0xfff8);fat(1,end)
    def entry(slot,name,start,size=0,attr=0,sector=None):
        off=(base+2*fatsiz if sector is None else sector)*512+slot*32
        b[off:off+11]=name.ljust(11,b' ')
        b[off+11]=attr
        struct.pack_into('<H',b,off+26,start);struct.pack_into('<I',b,off+28,size)
    return b,fat,entry,end,data

