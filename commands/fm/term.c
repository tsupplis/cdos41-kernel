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
/* TERM.DAT layout and byte strings: original CODE76EC..7B0F and
 * commands/editmenu/menuio.a86. No ANSI/ESC-Y terminal assumption. */
#define TERM_LIMIT 4096
static char termdata[TERM_LIMIT],position[16],attribute[16];
static unsigned termseg,termsize,off_pending,on_pending;
static int serial,poslen,attrlen,posswap,attrbias,lastattr,attrvalue;
static int savedstate[4];
struct fm_term_queue {unsigned a,b,c;unsigned *buffer;char name[8];};
int FMTSTATE(),DATASEG();
static int tb(offset)
unsigned offset;
{return termseg ? farbyte(termseg,offset)&255 : termdata[offset]&255;}
static unsigned tw(offset)
unsigned offset;
{return tb(offset)|(tb(offset+1)<<8);}
static int tvalid(offset)
unsigned offset;
{
    int n;
    if(!offset)return 1;
    if(offset>=termsize)return 0;
    n=tb(offset);
    if(n&128)n=2;
    return n<termsize-offset;
}
static int tout(ch)
int ch;
{bdos(2,ch&255);return 1;}
static int tstring(offset)
unsigned offset;
{
    int n,i,v;
    if(!offset)return 1;
    n=tb(offset);
    if(n&128) {
        if(!attrlen)return 0;
        v=((attrvalue&tb(offset+1))|tb(offset+2))&255;
        attrvalue=v;attribute[attrlen-1]=v+attrbias;
        for(i=0;i<attrlen;++i)tout(attribute[i]);
    } else for(i=1;i<=n;++i)tout(tb(offset+i));
    return 1;
}
static int tcontrol(number)
int number;
{return tstring(tw(2048+2*number));}
static int tvalidate()
{
    unsigned p;int i,n;
    if(termsize<2074)return 0;
    p=tw(2048);if(!p || p>=termsize)return 0;
    n=tb(p);posswap=(n&128)!=0;n&=127;
    if(n<2 || n>15 || n>=termsize-p)return 0;
    poslen=n;for(i=0;i<n;++i)position[i]=tb(p+1+i);
    p=tw(2072);attrlen=0;
    if(p) {
        if(p>=termsize)return 0;
        n=tb(p);if(n<1 || n>15 || n>=termsize-p)return 0;
        attrlen=n;for(i=0;i<n;++i)attribute[i]=tb(p+1+i);
        attrbias=attribute[n-1]&255;attrvalue=0;
    }
    for(i=512;i<2048;i+=2) {
        p=tw(i);if(!tvalid(p))return 0;
        if(p && (tb(p)&128) && !attrlen)return 0;
    }
    for(i=2050;i<2072;i+=2)if(!tvalid(tw(i)))return 0;
    return 1;
}
static int tload(current)
int current;
{
    char fcb[36];unsigned seg;struct fm_term_queue qpb;
    int user,i,j,n,opened,result;
    FMTSTATE(savedstate);user=bdos(32,255)&255;
    opened=result=0;termseg=termsize=0;
    bdos(32,0);bdos(44,1);bdos(51,DATASEG());
    for(i=0;i<36;++i)fcb[i]=0;
    for(i=1;i<12;++i)fcb[i]=' ';
    fcb[0]=16;fcb[1]='T';fcb[2]='E';fcb[3]='R';fcb[4]='M';
    fcb[9]='D';fcb[10]='A';fcb[11]='T';
    n=current+1;i=5;if(n>=10)fcb[i++]='0'+n/10;
    fcb[i]='0'+n%10;
    opened=(bdos(15,fcb)&255)!=255;
    if(!opened) {
        qpb.a=qpb.b=qpb.c=0;qpb.buffer=&seg;
        for(i=0;i<8;++i)qpb.name[i]="termdat "[i];
        if((bdos(135,&qpb)&65535)!=65535) {
            seg=0;
            if((bdos(137,&qpb)&65535)!=65535) {
                j=bdos(139,&qpb);
                if(seg && (j&65535)!=65535) {
                    termseg=seg;termsize=65535;result=tvalidate();goto finish;
                }
            }
            goto finish;
        }
        fcb[5]=fcb[6]=' ';
        opened=(bdos(15,fcb)&255)!=255;
        if(!opened)goto finish;
    }
    if((bdos(35,fcb)&255)==255 || fcb[35])goto finish;
    n=(fcb[33]&255)|((fcb[34]&255)<<8);
    if(n<17 || n>TERM_LIMIT/128)goto finish;
    for(i=0;i<n;++i) {
        bdos(26,termdata+128*i);
        if((bdos(20,fcb)&255)!=0)goto finish;
    }
    termsize=n*128;result=tvalidate();
finish:
    if(opened && (bdos(16,fcb)&255)==255)result=0;
    bdos(32,user);bdos(44,savedstate[3]);
    bdos(51,savedstate[1]);bdos(26,savedstate[0]);
    return result;
}
static int tcell(row,column,ch,attr)
int row,column,ch,attr;
{
    int i,a,b;unsigned on,off;
    if(row<0 || row>=24 || column<0 || column>=80)return 0;
    /* The original avoids scrolling the last cell when wrap-off is absent. */
    if(row==23 && column==79 && !tw(2058))return 1;
    a=posswap?column:row;b=posswap?row:column;
    for(i=0;i<poslen;++i) {
        if(i==poslen-2)tout((position[i]&255)+a);
        else if(i==poslen-1)tout((position[i]&255)+b);
        else tout(position[i]);
    }
    attr&=127;ch&=255;
    if(attr!=lastattr) {if(!tstring(tw(1536+2*attr)))return 0;lastattr=attr;}
    on=tw(512+2*ch);off=tw(1024+2*ch);
    if(!on || on!=on_pending || off!=off_pending) {
        if(!tstring(off_pending) || !tstring(on))return 0;
        on_pending=on;off_pending=off;
    }
    if(row==23 && column==79)tcontrol(5);
    tout(tb(256+ch));
    if(row==23 && column==79)tcontrol(4);
    return 1;
}
int fm_term_cursor(visible)
int visible;
{
    if(!ready)return 0;
    if(serial)return tcontrol(visible?6:7);
    bdos(6,27);bdos(6,visible?'e':'f');return 1;
}


static int acquire()
{
    if (!ready) return 0;
    if (held) return 1;
    if (!serial && !lock(xdata,screen,0)) return 0;
    held=1;
    return 1;
}
static int release()
{
    if (!ready) return 0;
    if (!held) return 1;
    if(serial) {held=0;return 1;}
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
    if(serial)return tcell(row,column,ch,attr);
    farput(image,2*(row*80+column),((attr&127)<<8)|(ch&255));
    return 1;
}
static int put(ch)
int ch;
{
    if (!ready || held) return 0;
    if(serial)return tout(ch);
    bdos(6,ch&255);
    return 1;
}
static int readkey()
{
    if (!ready || held) return -2;
    {
        int key,i;
        static char source[]={1,2,3,4,5,22,23,24,25,26,7,12,14,15,16,17,18,19,20,21,6};
        static char target[]={187,188,189,190,191,192,193,194,195,196,225,226,227,228,229,230,231,232,233,234,210};
        key=fm_native_key();
        if(serial && key>=0)for(i=0;i<21;++i)if(key==(source[i]&255))key=target[i]&255;
        return key;
    }
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
    serial=farword(xdata,candidate+24)!=0xb000 && farword(xdata,candidate+24)!=0xb800;
    if(serial) {
        if(!tload(current))return 0;
        bdos(109,0x8e);lastattr=-1;off_pending=on_pending=0;
    } else if (!segment) return 0;
    screen=candidate;image=segment;number=current;held=0;ready=1;
    /* ESC 6 returns raw function/keypad codes, as required by keys.c.
     * Preserve this console's prior expansion mode (XIOS VS offset 51).
     * No BDOS output is performed while holding its screen mutex.
     */
    if(!serial) {
        expansion=farbyte(xdata,screen+51);
        bdos(6,27);bdos(6,'6');
    }
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
    if(serial) {
        tstring(off_pending);off_pending=on_pending=0;
        tstring(tw(1536+14));tcontrol(6);bdos(109,savedstate[2]);
    } else {bdos(6,27);bdos(6,expansion ? '7' : '6');}
    ready=0;
    return 1;
}
