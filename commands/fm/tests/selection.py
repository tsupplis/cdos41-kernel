"""Subset input/matching, immutable rejection and native bridge contracts."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "select.h"
unsigned short XDATA;
static int version=0x1441,current=1,selects;
int XINIT(void) {XDATA=0x1234;return 0;}
int FARWORD(int seg,int off) {
    assert(seg==XDATA && off>=0xc18 && off<=0xc36 && !(off&1));
    return off==0xc18 || off==0xc1a ? 0x2000:0;
}
/* Old-style bridge declarations match DR C's mixed pointer/word arguments. */
int BDOS();
#include "selectio.c"
int BDOS(fn,arg) int fn;intptr_t arg; {
    char **packet;
    if(fn==12)return version;
    if(fn==25)return current;
    if(fn==14){current=arg;++selects;return 0;}
    assert(fn==152);packet=(char**)arg;
    if(!strcmp(packet[0],"bad"))return 255;
    memset(packet[1],0,36);memset(packet[1]+1,' ',11);
    if(!strcmp(packet[0],"*.txt"))memcpy(packet[1]+1,"????????TXT",11);
    else memcpy(packet[1]+1,"FILE    TXT",11);
    return 0;
}
int main(void) {
    struct fm_input in;
    char mask[11],previous[11],entry[32];int i;
    fm_input_open(&in);
    for(i=0;i<20;++i)fm_input_key(&in,'A');
    assert(in.length==12 && !in.text[12]);
    assert(fm_input_key(&in,8)==1 && in.length==11);
    assert(fm_input_key(&in,13)==2 && in.active);
    assert(fm_input_key(&in,27)==-1 && !in.active);
    memset(mask,'?',11);memcpy(previous,mask,11);
    assert(!fm_native_subset("bad",mask) && !memcmp(mask,previous,11));
    assert(!fm_native_subset("FILE.TXT",mask) && !memcmp(mask,previous,11));
    assert(!fm_native_subset("TOOLONGNAM.TXT",mask));
    assert(fm_native_subset("*.txt",mask));
    memset(entry,0,32);memcpy(entry+1,"ABC     TXT",11);
    assert(fm_subset_match(mask,entry));
    entry[9]|=128;assert(fm_subset_match(mask,entry));
    entry[10]='Z';assert(!fm_subset_match(mask,entry));
    assert(fm_native_drives()==3);
    assert(!fm_native_drive(0) && !fm_native_drive(17) && !fm_native_drive(3) && !selects);
    assert(fm_native_drive(1) && current==0 && selects==1);
    version=0x1431;assert(!fm_native_drives() && !fm_native_drive(2) && selects==1);
    return 0;
}
"""
# selectio.c includes the same declarations; avoid duplicate struct definition.
source=source.replace('#include "select.h"','')
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
    subprocess.run(['cc','-Wno-deprecated-non-prototype','-I',str(root),str(src),str(root/'select.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: bounded subset input, wildcard masks, attributes, rejection, drive table and guard')
