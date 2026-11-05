"""Directory entry uses extended open only, preserving literal dot names."""
from pathlib import Path
import tempfile,subprocess
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <stdint.h>
#include <string.h>
static int version=0x1441, opens, fail;
static char received[36];
static int mock(int fn,intptr_t arg) {
    if(fn==12)return version;
    assert(fn==15);++opens;memcpy(received,(void*)arg,36);return fail?255:0;
}
#define __BDOS(fn,arg) (mock(fn,(intptr_t)(arg))&255)
#define FM_TEST_ENTER
#include "native.c"
int BDOS(fn,arg) int fn;intptr_t arg; {return mock(fn,arg);}
int main(void) {
    char entry[32];int i;
    memset(entry,0,32);memset(entry+1,' ',11);entry[1]=entry[2]='.';entry[16]=64;
    assert(fm_native_enter(2,entry) && opens==1);
    assert((received[0]&255)==130 && !memcmp(received+1,entry+1,11));
    for(i=12;i<36;++i)assert(!received[i]);
    fail=1;assert(!fm_native_enter(2,entry) && opens==2);
    version=0x1431;assert(!fm_native_enter(2,entry) && opens==2);
    version=0x1441;entry[16]=0;assert(!fm_native_enter(2,entry) && opens==2);
    entry[16]=64;assert(!fm_native_enter(17,entry) && opens==2);
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
    subprocess.run(['cc','-Wno-deprecated-non-prototype','-I',str(root),str(src),
        str(root/'scan.c'),str(root/'dirlist.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: directory extended open, dot-dot, failure and OS/type guards')
