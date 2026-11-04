"""Read-only native checks on disposable CDOS and FAT floppy images."""
from pathlib import Path
import argparse
import hashlib
import subprocess
import tempfile

COMMAND = Path(__file__).resolve().parents[1]
ROOT = COMMAND.parents[1]
MEDIA = ROOT / 'media'


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def screen(path):
    data = path.read_bytes()
    return '\n'.join(data[i:i+160:2].decode('cp437').rstrip()
                     for i in range(0, 4000, 160))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fat16', action='store_true')
    parser.add_argument('--repair', action='store_true')
    parser.add_argument('--recover', action='store_true')
    parser.add_argument('--deleted', action='store_true')
    parser.add_argument('--contiguous', action='store_true')
    parser.add_argument('--directories', action='store_true')
    parser.add_argument('--read-test', action='store_true')
    args = parser.parse_args()
    if args.directories and (args.repair or args.recover or args.contiguous or args.deleted): parser.error('--directories uses a separate R/RF fixture')
    if args.recover: args.repair=True
    if args.contiguous and (args.repair or args.deleted): parser.error('--contiguous uses a separate L/LF fixture')
    if args.deleted and args.repair: parser.error('--deleted tests D/DF independently of repair fixtures')
    with tempfile.TemporaryDirectory(prefix='chkdosfs-live-') as temporary:
        folder = Path(temporary)
        twist = str(ROOT / 'tools/cpm86twist.py')
        logical = folder / 'logical.img'
        run('python3', twist, 'untwist', str(MEDIA / 'base.img'), str(logical), cwd=MEDIA)
        data = bytearray(logical.read_bytes())
        data[:4096] = (ROOT / 'boot/boottrack.bin').read_bytes()
        logical.write_bytes(data)
        run('cpmcp', '-f', 'ccpm86-320', str(logical),
            str(ROOT / 'kernel/sysgen/ccpm.sys'), str(COMMAND / 'chkdosfs.cmd'),
            '0:', cwd=MEDIA)
        run('python3', twist, 'twist', str(logical), str(folder / 'system.img'), cwd=MEDIA)
        if args.fat16:
            run('mformat', '-C', '-i', str(folder / 'fat.img'), '-t', '305',
                '-h', '4', '-n', '17', '-c', '2', '::', cwd=folder)
        else:
            run('mformat', '-C', '-i', str(folder / 'fat.img'), '-f', '360', '::', cwd=folder)
        (folder / 'test.txt').write_bytes(b'native FAT check\r\n' * 100)
        run('mcopy', '-i', 'fat.img', 'test.txt', '::TEST.TXT', cwd=folder)
        run('mmd', '-i', 'fat.img', '::SUB', cwd=folder)
        run('mcopy', '-i', 'fat.img', 'test.txt', '::SUB/NESTED.TXT', cwd=folder)
        clean = (folder / 'fat.img').read_bytes()
        cfg = (MEDIA / 'cdos86.cfg').read_text()
        cfg = cfg.replace('path = "rom"', f'path = "{MEDIA / "rom"}"')
        cfg = cfg.replace('"cdos86.img"', '"system.img"').replace('"cdostools.img"', '"fat.img"')
        cfg = cfg.replace('speed = 16', 'speed = 64')
        cfg = cfg.replace('driver = "sdl"', 'driver = "null"')
        cfg = cfg.replace('driver      = "sdl:lowpass=5000"', 'driver      = "null"')
        if args.fat16:
            run('mformat','-C','-i',str(folder/'floppy.img'),'-f','360','::',cwd=folder)
            cfg = cfg.replace('file     = "fat.img"','file     = "floppy.img"')
            cfg += '\ndisk {\n drive = 0x80\n type = "auto"\n file = "hard.img"\n' + \
                   ' c = 306\n h = 4\n s = 17\n optional = 0\n}\n'
        (folder / 'test.cfg').write_text(cfg)
        for damaged in ((False,) if args.deleted or args.contiguous or args.directories or args.read_test else (True,) if args.repair else (False, True)):
            disk = bytearray(clean)
            reserved = int.from_bytes(disk[14:16], 'little')
            fatsize = int.from_bytes(disk[22:24], 'little')
            def setfat(image,cluster,value):
                for copy in range(disk[16]):
                    off=(reserved+copy*fatsize)*512+(cluster*2 if args.fat16 else cluster*3//2)
                    if args.fat16: packed=value
                    else:
                        packed=int.from_bytes(image[off:off+2],'little')
                        packed=(packed&15)|(value<<4) if cluster&1 else (packed&0xf000)|value
                    image[off:off+2]=packed.to_bytes(2,'little')
            root=(reserved+disk[16]*fatsize)*512
            roots=int.from_bytes(disk[17:19],'little')
            test=next(at for at in range(root,root+roots*32,32)
                      if disk[at:at+11]==b'TEST    TXT')
            if args.recover:
                cluster=int.from_bytes(disk[test+26:test+28],'little')
                count=0
                while True:
                    count+=1
                    off=reserved*512+(cluster*2 if args.fat16 else cluster*3//2)
                    link=int.from_bytes(disk[off:off+2],'little')
                    if not args.fat16: link=link>>4 if cluster&1 else link&4095
                    if link>=(0xfff8 if args.fat16 else 0xff8): break
                    cluster=link
                last=cluster
                setfat(disk,last,0)
                disk[test+28:test+32]=(1000000).to_bytes(4,'little')
            if args.repair:
                setfat(disk,341,342 if args.recover else (0xffff if args.fat16 else 0xfff))
            elif damaged:
                disk[(reserved + fatsize)*512+3] ^= 1
            if args.contiguous:
                chain=[];cluster=int.from_bytes(disk[test+26:test+28],'little')
                while True:
                    chain.append(cluster)
                    off=reserved*512+(cluster*2 if args.fat16 else cluster*3//2)
                    link=int.from_bytes(disk[off:off+2],'little')
                    if not args.fat16: link=link>>4 if cluster&1 else link&4095
                    if link>=(0xfff8 if args.fat16 else 0xff8):break
                    cluster=link
                assert chain==list(range(chain[0],chain[0]+len(chain)))
                assert int.from_bytes(disk[test+32+26:test+32+28],'little')==chain[0]+len(chain)
                restored=bytes(disk)
                for cluster in chain:setfat(disk,cluster,0)
            if args.deleted:
                base=reserved+disk[16]*fatsize+(roots+15)//16
                at=(base+(40-2)*disk[13])*512
                dot=bytearray(64)
                dot[:11]=b'.          ';dot[11]=16
                dot[26:28]=(40).to_bytes(2,'little')
                dot[32:43]=b'..         ';dot[43]=16
                disk[at:at+64]=dot
            if args.directories:
                directory=next(at for at in range(root,root+roots*32,32) if disk[at:at+11]==b'SUB        ')
                head=int.from_bytes(disk[directory+26:directory+28],'little')
                disk[directory]=229
            expected=bytearray(restored if args.contiguous else disk)
            if args.directories:
                record=bytearray(32)
                record[:11]=('FILE%04XCHK'%head).encode('ascii');record[11]=16
                record[26:28]=head.to_bytes(2,'little')
                expected[directory:directory+32]=record
            if args.recover:
                end=0xffff if args.fat16 else 0xfff
                setfat(expected,last,end);setfat(expected,341,end)
                expected[test+28:test+32]=(count*disk[13]*512).to_bytes(4,'little')
                slot=next(at for at in range(root,root+roots*32,32) if disk[at] in (0,229))
                rec=bytearray(32);rec[:11]=b'FILE0155CHK';rec[11]=32
                rec[26:28]=(341).to_bytes(2,'little')
                rec[28:32]=(disk[13]*512).to_bytes(4,'little')
                expected[slot:slot+32]=rec
                if disk[slot]==0 and slot+32<root+roots*32: expected[slot+32]=0
            elif args.repair: setfat(expected,341,0)
            (folder / 'fat.img').write_bytes(disk)
            if args.fat16:
                hard = bytearray(306*4*17*512)
                hard[68*512:68*512+len(disk)] = disk
                part = bytearray(16)
                part[1:4] = bytes([0,1,1])
                part[4] = 4
                part[5:8] = bytes([3,0x51,0x31])
                part[8:12] = (68).to_bytes(4,'little')
                part[12:16] = (len(disk)//512).to_bytes(4,'little')
                hard[446:462] = part
                hard[510:512] = b'\x55\xaa'
                (folder/'hard.img').write_bytes(hard)
            before = {name: hashlib.sha256((folder/name).read_bytes()).digest()
                      for name in (('fat.img','system.img','hard.img') if args.fat16 else ('fat.img','system.img'))}
            if args.repair or args.contiguous or args.directories:
                if args.fat16:
                    after=bytearray(hard)
                    after[68*512:68*512+len(expected)]=expected
                    before['hard.img']=hashlib.sha256(after).digest()
                else: before['fat.img']=hashlib.sha256(expected).digest()
            commands = ['c f000000']
            def command(text):
                for char in text:
                    key = {':': '+Shift Semicolon -Shift', ' ': 'Space', '/': 'Slash'}.get(char,char)
                    commands.extend(['key '+key, 'c 200000'])
                commands.extend(['key Return','c '+('50000000' if args.fat16 else '20000000')])
            first='r' if args.directories else 'l' if args.contiguous else 'd' if args.deleted else 'f' if args.repair else ''
            if args.read_test:first+='b'
            command('a:chkdosfs '+('c:' if args.fat16 else 'b:')+(' /'+first if first else ''))
            if args.repair:
                commands.extend(['key '+('y' if args.recover else 'n'),
                                 'c '+('50000000' if args.recover and args.fat16 else '20000000' if args.recover else '1000000')])
                commands.extend(['key y','c '+('50000000' if args.fat16 else '20000000')])
            commands.append('save "result.bin" bin b800:0000 fa0')
            second='rfv' if args.directories else 'lfv' if args.contiguous else 'dfv' if args.deleted else 'v'
            if args.read_test:
                if not (args.directories or args.contiguous or args.deleted or args.repair):second='bfv'
                else:second+='b'
            command('a:chkdosfs '+('c:' if args.fat16 else 'b:')+' /'+second)
            if args.contiguous or args.directories:
                commands.append('save "prompt.bin" bin b800:0000 fa0')
                commands.extend(['key y','c '+('50000000' if args.fat16 else '20000000')])
            commands.append('save "repeat.bin" bin b800:0000 fa0')
            if args.directories and not args.fat16:
                command('b:');command('dir')
                commands.append('save "os-view.bin" bin b800:0000 fa0')
            commands.append('q')
            with (folder/'pce.log').open('wb') as log:
                subprocess.run(['pce-ibmpc','-c','test.cfg','-t','null','-g','vga'],
                    cwd=folder,input=('\n'.join(commands)+'\n').encode(),
                    stdout=log,stderr=log,timeout=120 if args.fat16 else 60,check=True)
            if args.directories and not args.fat16:
                listing=screen(folder/'os-view.bin')
                assert ('\\FILE%04X'%head) in listing or (('FILE%04X'%head) in listing and '<DIR>' in listing),listing
            for name,digest in before.items():
                assert hashlib.sha256((folder/name).read_bytes()).digest()==digest,name
            if args.contiguous or args.directories:
                assert ('Recover validated first-level directories' if args.directories else 'Rebuild candidate contiguous file chains') in screen(folder/'prompt.bin')
            for capture in ('result.bin','repeat.bin'):
                text=screen(folder/capture)
                if ((args.contiguous or args.directories) and capture=='result.bin') or (not args.contiguous and not args.directories and (not args.recover or capture=='repeat.bin')):
                    assert ('Drive C  FAT16' if args.fat16 else 'Drive B  FAT12') in text,text
                assert ('Changes written.' if (args.repair and capture=='result.bin') or ((args.contiguous or args.directories) and capture=='repeat.bin') else 'No changes written.') in text,text
                if args.deleted: assert 'Erased directory remnants: 1' in text,text
                if args.read_test:
                    assert 'File/directory data sectors read: '+str((6 if args.recover else 5)*disk[13]) in text,text
                if capture=='repeat.bin':
                    assert 'TEST.TXT' in text and 'NESTED.TXT' in text,text
                    if args.recover: assert 'FILE0155.CHK' in text,text
                if args.directories:
                    assert 'Directory recovery candidates: '+('1' if capture=='result.bin' else '0') in text,text
                if args.contiguous:
                    assert 'Contiguous-chain candidates: '+('1' if capture=='result.bin' else '0') in text,text
                assert 'Consistency errors: '+('1' if (args.contiguous or args.directories) and capture=='result.bin' else '1' if damaged and not args.repair else '0') in text,text
            print('PASS: native '+('RB detection and confirmed RBF recovery' if args.read_test and args.directories else 'B/BF data reads' if args.read_test and not args.repair else 'R detection and confirmed RF root-only directory recovery' if args.directories else 'L detection and confirmed LF contiguous rebuild' if args.contiguous else 'D and DF diagnostic-only remnant scan' if args.deleted else 'EOF/size correction and recovered file' if args.recover else 'confirmed lost-cluster repair' if args.repair else 'FAT mirror mismatch' if damaged else ('clean nested FAT16' if args.fat16 else 'clean nested FAT12'))+
                  (', clean verification and exact expected metadata changes' if args.repair or args.contiguous or args.directories else ', repeat invocation and unchanged disk images'))

if __name__ == '__main__':
    main()
