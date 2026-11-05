"""Read-only menu controller: focus, boundaries, scrolling and setup return."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include "focus.h"
int main(void) {
    struct fm_focus f;
    int n;
    assert(!fm_focus_open(&f,0));
    assert(fm_focus_open(&f,5));
    assert(fm_focus_key(&f,0xc4)==-1); /* F10 is not menu focus */
    assert(fm_focus_key(&f,9)==1 && f.active);
    assert(fm_focus_key(&f,0xd0)==1 && fm_focus_index(&f)==1);
    assert(fm_focus_key(&f,0xcf)==1 && fm_focus_index(&f)==16);
    assert(f.navigation.offset+f.navigation.capacity>=17);
    assert(fm_focus_key(&f,13)==1 && f.setup && fm_focus_index(&f)==17);
    assert(fm_focus_key(&f,0xcf)==1 && fm_focus_index(&f)==27);
    assert(fm_focus_key(&f,13)==2 && fm_focus_index(&f)==27); /* no side effect */
    assert(fm_focus_key(&f,27)==1 && !f.setup && fm_focus_index(&f)==16);
    assert(f.navigation.offset+f.navigation.capacity>=17);
    assert(fm_focus_key(&f,27)==1 && !f.active);
    assert(fm_focus_key(&f,27)==-1);
    for(n=1;n<=24;++n) {
        fm_focus_open(&f,n);fm_focus_key(&f,9);
        fm_focus_key(&f,0xcf);fm_focus_key(&f,13);
        fm_focus_key(&f,0xcf);fm_focus_key(&f,27);
        assert(f.navigation.selected==17 && !f.setup);
        assert(f.navigation.offset<=16 && f.navigation.offset+n>=17);
    }
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
    subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),str(src),
       str(root/'focus.c'),str(root/'menu.c'),str(root/'navigate.c'),str(root/'keys.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: Tab focus, F10 passthrough, menu scrolling, setup return, inactive actions')
