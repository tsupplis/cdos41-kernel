/* Local WINDOW-style gateway; ABI: kernel/con/xcon2.lib.
 * Virtual text image is 24x80 words; status line is outside this image.
 */
#include "frame.h"
#include "conio.h"
#include "term.h"
#define xinit XINIT
#define xcall XCALL
#define farword FARWORD
#define farbyte FARBYTE
#define farput FARPUT
#define lock FMLOCK
#define bdos BDOS
#define xdata XDATA
unsigned short xdata=0;
int xinit(),xcall(),farword(),farbyte(),farput(),lock(),bdos();
static unsigned screen, image;
static int number, ready, held, expansion;

static int acquire()
{
    if (!ready) return 0;
    if (held) return 1;
    if (!lock(xdata,screen,0)) return 0;
    held=1;
    return 1;
}
static int release()
{
    if (!ready) return 0;
    if (!held) return 1;
    if (!lock(xdata,screen,1)) return 0;
    held=0;
    /* Repaint the current physical window after changing its virtual image. */
    xcall(20,farword(xdata,screen+4),farword(xdata,screen+2),number);
    return 1;
}
static int cell(row,column,ch,attr)
int row,column,ch,attr;
{
    if (!ready || !held || row<0 || row>=24 || column<0 || column>=80)
        return 0;
    farput(image,2*(row*80+column),((attr&127)<<8)|(ch&255));
    return 1;
}
static int put(ch)
int ch;
{
    if (!ready || held) return 0;
    bdos(6,ch&255);
    return 1;
}
static int readkey()
{
    if (!ready || held) return -2;
    return fm_native_key();
}
int fm_term_open(canvas,console)
struct fm_canvas *canvas;
struct fm_console *console;
{
    unsigned status, candidate, segment;
    int version, count, current;
    if (!canvas || !console || ready) return 0;
    version=bdos(12,0);
    /* This private backend is scoped to the project's CDOS 4.1 ABI. */
    if ((version&0xffff)!=0x1441) return 0;
    xinit();
    status=xcall(16,0,0,255);
    if (!status || status>65530) return 0;
    count=farbyte(xdata,status+1);
    current=bdos(153,0)&255;
    if (count<1 || count>16 || current>=count) return 0;
    candidate=xcall(16,0,0,current);
    if (!candidate || candidate>65482) return 0;
    segment=farword(xdata,candidate+22);
    if (!segment) return 0;
    screen=candidate;image=segment;number=current;held=0;ready=1;
    /* ESC 6 returns raw function/keypad codes, as required by keys.c.
     * Preserve this console's prior expansion mode (XIOS VS offset 51).
     * No BDOS output is performed while holding its screen mutex.
     */
    expansion=farbyte(xdata,screen+51);
    bdos(6,27);bdos(6,'6');
    canvas->rows=24;canvas->columns=80;canvas->cell=cell;
    /* Runtime assignments avoid DR C static callback relocation defects. */
    console->acquire=acquire;console->release=release;
    console->put=put;console->read=readkey;console->held=0;
    return 1;
}
int fm_term_close(console)
struct fm_console *console;
{
    if (!ready) return 1;
    if (!console || !fm_console_end(console)) return 0;
    bdos(6,27);bdos(6,expansion ? '7' : '6');
    ready=0;
    return 1;
}
