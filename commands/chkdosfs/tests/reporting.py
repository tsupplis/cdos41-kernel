#!/usr/bin/env python3
"""Original CHKDSK label/allocation reporting, using the production C core."""
from pathlib import Path
import struct,subprocess,tempfile
from fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
count=0
with tempfile.TemporaryDirectory(prefix='chkdosfs-report-') as tmp:
    tmp=Path(tmp);exe=tmp/'check'
    subprocess.run(['cc','-std=gnu89','-Wno-implicit-int','-Wno-return-type',
                    '-Wno-deprecated-non-prototype','-I',str(ROOT),str(ROOT/'fat.c'),
                    str(ROOT/'check.c'),str(ROOT/'tests/host.c'),'-o',str(exe)],check=True)
    for bits in (12,16):
        for spc in (1,4):
            for stamp in (None,(2026,11,4,16,35),(1980,1,1,0,0),(2026,15,1,0,0),(2026,1,1,31,0),(2026,1,1,0,63)):
                b,f,e,end,data=fixture(bits,spc=spc)
                f(2,end);e(0,b'USER    TXT',2,1)
                f(3,4);f(4,end);e(1,b'HIDDEN  TXT',3,spc*1024-3,attr=2)
                f(5,6);f(6,end);e(2,b'SUB',5,attr=16)
                e(0,b'.',5,attr=16,sector=data+3*spc)
                e(1,b'..',0,attr=16,sector=data+3*spc)
                if stamp:
                    e(3,b'TEST LABEL ',0,attr=8)
                    year,month,day,hour,minute=stamp
                    root=1+2*int.from_bytes(b[22:24],'little')
                    struct.pack_into('<HH',b,root*512+3*32+22,(hour<<11)|(minute<<5),((year-1980)<<9)|(month<<5)|day)
                image=tmp/'disk.img';image.write_bytes(b)
                p=subprocess.run([str(exe),str(image)],capture_output=True,text=True,check=True)
                expected=f'{5*spc*512} bytes allocated: files {spc*512}, hidden {2*spc*512}, directories {2*spc*512}'
                assert expected in p.stdout,p.stdout
                assert f'{(700 if bits==12 else 6000)*spc*512} bytes total disk space' in p.stdout,p.stdout
                assert ('Volume TEST LABEL' in p.stdout)==bool(stamp),p.stdout
                if stamp:
                    if month<=12 and hour<24 and minute<60:
                        assert f'created {year}-{month:02}-{day:02} {hour}:{minute:02}' in p.stdout,p.stdout
                    else:assert 'timestamp absent or invalid' in p.stdout,p.stdout
                assert image.read_bytes()==b
                count+=1
            # Candidate-tree probes must not inflate live allocation totals.
            f(10,end);e(0,b'.',10,attr=16,sector=data+8*spc)
            e(1,b'..',0,attr=16,sector=data+8*spc)
            image.write_bytes(b)
            p=subprocess.run([str(exe),str(image),'-1','N','-1','0','0','-1','0','1'],capture_output=True,text=True)
            assert p.returncode==1 and expected in p.stdout,p.stdout
            assert 'Directory recovery candidates: 1' in p.stdout,p.stdout
            assert image.read_bytes()==b
            count+=1
print(f'PASS: {count} label/allocation-report cases; exact totals, bounded timestamps and unchanged images')
