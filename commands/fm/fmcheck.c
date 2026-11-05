/* Noninteractive regression executable. This is not the replacement FM. */
#include "fm.h"
#include "menu.h"
#include "screen.h"
#ifdef HOST_TEST
#include <stdio.h>
#else
int printf();
#endif
int failures;
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
    char *p, *before;
    unsigned value;
    int i;
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
