/* Noninteractive regression executable. This is not the replacement FM. */
#include "fm.h"
#include "menu.h"
#include "screen.h"
#include "browse.h"
#include "keys.h"
#include "dirlist.h"
#include "scan.h"
#include "conio.h"
#ifdef HOST_TEST
#include <stdio.h>
#else
int printf();
#endif
int failures;
static int console_events;
static int console_acquire() { console_events=console_events*10+1; return 1; }
static int console_release() { console_events=console_events*10+2; return 1; }
static int console_put(ch)
int ch;
{ console_events=console_events*10+3; return ch==65; }
static int console_read() { return 0xc8; }

static char screen_bytes[8];
static int screen_length;
static int capture(bytes, length)
char *bytes;
int length;
{
    int i;
    if (length > 8) return 0;
    for (i=0; i<length; ++i) screen_bytes[i]=bytes[i];
    screen_length=length;
    return 1;
}
static verify(ok, name)
int ok;
char *name;
{
    if (!ok) { printf("FAIL: %s\n", name); ++failures; }
    return 0;
}
main()
{
    struct fm_config config;
    struct fm_screen screen;
    struct fm_layout layout;
    struct fm_navigation navigation;
    struct fm_browser browser;
    struct fm_console console;
    static int file_row[]={0,0,0,3,0};
    static int file_col[]={0,0,20,0,0};
    static int file_width[]={60,80,60,80,80};
    static int file_height[]={21,18,21,18,20};
    char *p, *before;
    unsigned value;
    char name[FM_NAME_SIZE];
    char *names[3];
    int i;
#ifndef HOST_TEST
    static struct fm_file files[128];
    static char saved_dma[128];
    int count, found, result;
    __BDOS(26,saved_dma);
    result=fm_native_scan(1,0,0,files,128,&count,saved_dma);
    found=0;
    for (i=0;i<count;++i)
        if (files[i].name[0]=='F' && files[i].name[1]=='M' &&
            files[i].name[2]=='P' && files[i].name[3]=='R') found=1;
    verify(result==1 && found,"native read-only directory search");
#endif
    for (i=0;i<FM_CONFIG_COUNT;++i) config.value[i]=0;
    config.value[8]=17; config.value[9]=1; config.value[11]=2;
    for (i=0;i<5;++i) {
        config.value[1]=i+1;
        verify(fm_layout_calculate(&layout,&config,24,80,0) &&
            layout.files.row==file_row[i] && layout.files.column==file_col[i] &&
            layout.files.width==file_width[i] && layout.files.height==file_height[i] &&
            layout.prompt.row==21 && layout.prompt.width==80,"native menu geometry");
    }
    config.value[1]=2;
    verify(fm_layout_calculate(&layout,&config,24,80,1) &&
        layout.menu.height==8 && layout.files.height==13,"expanded bottom menu");
    verify(fm_key_normalize(0xc8)==11 && fm_key_normalize(0xd0)==10 &&
        fm_key_normalize(0xcb)==8 && fm_key_normalize(0xcd)==12,"navigation key normalization");
    verify(fm_key_translate(65,"AB","BC",2)==67,"cascading terminal key map");
    verify(fm_key_normalize(27)==27,"escape passthrough");
    navigation.count=8; navigation.selected=6; navigation.offset=0;
    navigation.capacity=6; navigation.columns=3;
    verify(fm_navigate(&navigation,10)==1 && navigation.selected==6 &&
        navigation.offset==3,"incomplete final row scroll");
    navigation.selected=1; navigation.offset=0;
    verify(fm_navigate(&navigation,8)==1 && navigation.selected==8 &&
        navigation.offset==3,"left wraps to final item");
    verify(fm_directory_name("\0TEST    CMD",name,FM_NAME_SIZE) &&
        name[4]=='.' && name[7]=='D' && name[8]==' ' && name[12]==0,
        "directory display name");
    names[0]="Z.CMD       "; names[1]="A.TXT       "; names[2]="A.CMD       ";
    verify(fm_directory_sort(names,3) && names[0][2]=='C' &&
        names[1][2]=='T' && names[2][0]=='Z',"directory name ordering");
    layout.files.row=0; layout.files.column=0;
    layout.files.width=30; layout.files.height=4;
    verify(fm_browser_open(&browser,names,3,&layout.files,14,7,112) &&
        fm_browser_key(&browser,0xcd)==1 && browser.navigation.selected==2,
        "browser key integration");
    console.acquire=console_acquire; console.release=console_release;
    console.put=console_put; console.read=console_read; console.held=0;
    console_events=0;
    verify(fm_console_begin(&console) && fm_console_write(&console,"A",1) &&
        console_events==1231 && console.held,"console output lock ordering");
    verify(fm_console_key(&console,0,0,0)==11 && !console.held,
        "console input releases lock and normalizes key");
    screen.rows=24; screen.columns=80; screen.write=capture;
    verify(fm_screen_position(&screen,23,79) && screen_length==4 &&
        screen_bytes[0]==27 && screen_bytes[1]=='Y' &&
        screen_bytes[2]==55 && screen_bytes[3]==111,"cursor protocol");
    screen_length=0;
    verify(!fm_screen_position(&screen,24,0) && screen_length==0,"row boundary");
    verify(!fm_screen_position(&screen,0,-1) && screen_length==0,"negative column");
    verify(fm_screen_cursor(&screen,0) && screen_length==2 &&
        screen_bytes[0]==27 && screen_bytes[1]=='f',"hide cursor protocol");
    verify(fm_screen_cursor(&screen,1) && screen_bytes[1]=='e',"show cursor protocol");
    verify(fm_menu_count==28 && fm_file_menu_count==17,"menu counts");
    verify(fm_menu_items[11].minimum==1 && fm_menu_items[11].maximum==1,"run selection bounds");
    verify(fm_menu_items[16].label[0]=='S',"setup menu entry");
    for (i=0; i<FM_CONFIG_COUNT; ++i) config.value[i]=99;
    p="OBJECT FG COLOR=0";
    verify(fm_config_assignment(&config,&p)==16 && config.value[2]==0 && !*p,"object foreground");
    p="key fg color=14";
    verify(fm_config_assignment(&config,&p)==28 && config.value[14]==14,"case-insensitive keyword");
    p="OBJECT  FG COLOR=3"; before=p;
    verify(!fm_config_assignment(&config,&p) && p==before,"extra keyword space");
    p="OBJECT FG COLOR =3"; before=p;
    verify(!fm_config_assignment(&config,&p) && p==before,"space before equals");
    p="OBJECT BG COLOR=  261 rest";
    verify(fm_config_assignment(&config,&p)==17 && config.value[3]==5 && *p==' ',"byte assignment and remainder");
    p=" 65536x"; value=42;
    verify(fm_config_number(&p,&value) && value==0 && *p=='x',"16-bit overflow");
    p="\t12"; before=p; value=42;
    verify(!fm_config_number(&p,&value) && value==42 && p==before,"tab rejected");
    p="-1"; before=p;
    verify(!fm_config_number(&p,&value) && p==before,"sign rejected");
    p="PROMPT FG COLOR=";
    verify(!fm_config_assignment(&config,&p) && !*p && config.value[6]==99,"missing value");
    p="NO SUCH KEY=1"; before=p;
    verify(!fm_config_assignment(&config,&p) && p==before,"unknown keyword");
    printf("FM configuration core: %s\n", failures ? "FAIL" : "PASS");
    return failures ? 1 : 0;
}
