"""Native backend contract checks with simulated XIOS; no kernel memory writes."""
from pathlib import Path
import subprocess, tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include "frame.h"
#include "conio.h"
#include "term.h"
extern unsigned short XDATA;
static int version=0x1441, count=4, current=2, image=0x3000;
static int initializations, locked, refresh, writes, address, value;
static int expansion=255, escape;
int BDOS(int function,int arg) {
    assert(!locked);
    if(function==12) return version;
    if(function==153) return current;
    assert(function==6);
    if(escape) { assert(arg=='6' || arg=='7'); expansion=arg=='7'?255:0;escape=0; }
    else { assert(arg==27);escape=1; }
    return 0;
}
int XINIT(void) { ++initializations;XDATA=0x1000;return 1; }
int XCALL(int function,int bx,int cx,int dx) {
    if(function==16) return dx==255 ? 0x100 : 0x200;
    assert(function==20 && !locked && bx==0x174f && cx==0 && dx==2);
    ++refresh;return 1;
}
int FARBYTE(int seg,int off) { assert(seg==0x1000);if(off==0x233)return expansion;assert(off==0x101);return count; }
int FARWORD(int seg,int off) {
    assert(seg==0x1000);
    if(off==0x218)return 0xb800;
    if(off==0x216) return image;
    if(off==0x204) return 0x174f;
    assert(off==0x202);return 0;
}
int FARPUT(int seg,int off,int word) {
    assert(locked && seg==image);++writes;address=off;value=word;return 1;
}
int FMLOCK(int seg,int off,int mode) {
    assert(seg==0x1000 && off==0x200);
    assert(locked==mode);locked=!mode;return 1;
}
int FMTSTATE(){assert(0);return 0;}
int DATASEG(){return 0;}
int fm_native_key(void) { assert(!locked);return -1; }
int main(void) {
    struct fm_canvas canvas;
    struct fm_console console;
    version=0x1431;assert(!fm_term_open(&canvas,&console) && !initializations);
    version=0x1441;count=0;assert(!fm_term_open(&canvas,&console));
    count=4;current=4;assert(!fm_term_open(&canvas,&console));
    current=2;image=0;assert(!fm_term_open(&canvas,&console));
    image=0x3000;assert(fm_term_open(&canvas,&console));
    assert(!expansion);
    assert(canvas.rows==24 && canvas.columns==80);
    assert(!canvas.cell(0,0,65,7));
    assert(fm_console_begin(&console) && locked);
    assert(canvas.cell(23,79,65,112) && address==3838 && value==0x7041);
    assert(!canvas.cell(24,0,65,7) && writes==1);
    assert(!console.put(65));
    assert(fm_console_end(&console) && !locked && refresh==1);
    assert(console.read()==-1);
    assert(fm_console_begin(&console));
    assert(fm_term_close(&console) && !locked && !console.held && refresh==2);
    assert(!canvas.cell(0,0,65,7) && console.read()==-2);
    assert(fm_term_close(&console) && expansion==255);
    expansion=0;assert(fm_term_open(&canvas,&console));
    assert(fm_term_close(&console) && !expansion);
    return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/'termcheck.c';src.write_text(source);exe=Path(tmp)/'termcheck'
    subprocess.run(['cc','-std=c89','-Wno-deprecated-non-prototype','-I',str(root),
        str(src),str(root/'term.c'),str(root/'conio.c'),str(root/'keys.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: CDOS guard, console discovery, locked cell writes, bounds, refresh and close cleanup (simulated XIOS)')
