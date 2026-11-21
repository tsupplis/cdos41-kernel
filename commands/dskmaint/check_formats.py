"""Validate format/menu bindings and BPBs in the actual linked DSKMAINT CMD."""
from pathlib import Path
import re
import struct

image=Path('dskmaint.cmd').read_bytes()
code_length=int.from_bytes(image[1:3],'little')*16
data=image[128+code_length:128+code_length+int.from_bytes(image[10:12],'little')*16]
maptext=Path('dskraw.map').read_text(errors='replace')
module=maptext.split('map for module:  SQUIDDM3A')[1].split('map for module:')[0]
base=int(re.search(r'\(0000:([0-9A-F]+)-[0-9A-F]+\)\s+DATA',module)[1],16)
symbols={name:int(offset,16)+base for offset,name in re.findall(r'([0-9A-F]{4})\s+([A-Z_@][A-Z0-9_@]*)',Path('squiddm3.sym').read_text(errors='replace'))}
def word(at):return int.from_bytes(data[at:at+2],'little')
def loc(name):return symbols[name.upper()]
labels=('dos_1_9','dos_2_9','cpm_1_8','cpm_2_8','dos_1_8','dos_2_8','dos_15','dos_720','dos_1440','cpm_720','cpm_1200','cpm_1440')
assert [word(loc('disk_type')+i*2) for i in range(12)]==[loc(n) for n in labels]
assert [word(loc('cpm_format_types')+i*2) for i in range(5)] == [4,6,18,20,22]
assert [word(loc('dos_format_types')+i*2) for i in range(5)] == [0,2,14,12,16]
assert data[loc('family_answer_keys'):loc('family_answer_keys')+3] == bytes([0xbc,0xbd,0x1b])
assert data[loc('capacity_answer_keys'):loc('capacity_answer_keys')+6] == bytes([0xbe,0xbf,0xc0,0xc1,0xc2,0x1b])
for name,spt,gap in [('cpm_720',9,0x50),('cpm_1200',15,0x54),('cpm_1440',18,0x6c)]:
    at=loc(name)
    assert struct.unpack_from('<5H',data,at) == (spt,160,2,512,spt*512)
    assert word(at+13) == 0xe500+gap
    assert word(at+19) == 160 and word(at+21) == 29
    assert word(at+23) == word(loc('cpm_2_8')+23)
    assert word(at+25) == 0 and word(at+27) == 0 and data[at+29] == 79
for label,cyl,spt,spc,media,spf,roots,total in [
 ('dos_1_9',40,9,1,0xfc,2,64,360),('dos_2_9',40,9,2,0xfd,2,112,720),
 ('dos_720',80,9,2,0xf9,3,112,1440),('dos_15',80,15,1,0xf9,7,224,2400),
 ('dos_1440',80,18,1,0xf0,9,224,2880)]:
    at=loc(label)
    heads=1 if label=='dos_1_9' else 2
    assert struct.unpack_from('<5H',data,at)==(spt,cyl*heads,heads,512,spt*512)
    assert word(at+19)==cyl*heads and word(at+21)==29 and data[at+29]==cyl-1
    assert struct.unpack_from('<HBHBHHBHHHH',data,word(at+27))==(512,spc,1,2,roots,total,media,spf,spt,heads,0)
    md=loc('dos_directory')+data[at+12]*3
    assert tuple(data[md:md+3])==(media,spf,roots//16)
assert data[loc('format_block'):loc('format_block')+72]==b''.join(bytes([0,0,n,2]) for n in range(1,19))
for family,sizes in [('cpm',(160,320,720,1200,1440)),('dos',(180,360,720,1200,1440))]:
    table=loc(family+'_keys')
    assert word(table) == 5
    for index,size in enumerate(sizes):
        at=loc('key_'+family+str(size))
        assert word(table+2+index*2) == at
        row,col=data[at:at+2]
        assert (row,col) == ((10,6),(10,31),(10,56),(14,6),(14,31))[index]
        assert data[at+2:at+5] == f'F{index+4} '.encode()
        assert word(at+5) == 1 and data[at+7] == row+1
        assert data[at+8] == col+7
        assert data[at+8]+word(word(at+9)) <= 79, 'Legend crosses screen frame'
for symbol,filename in [('boot','bootsect.bin'),('ldr','loader.bin')]:
    payload=Path(filename).read_bytes()
    assert data[loc(symbol):loc(symbol)+len(payload)] == payload
assert len(Path('dosbootx.bin').read_bytes())==512
assert Path('dosbootx.bin').read_bytes()[-2:]==b'\x55\xaa'
print('PASS: linked format tables, complete BPBs, FAT metadata, 18-sector CHRN table and separate CP/M/DOS F4-F8 menus and shared loader')
