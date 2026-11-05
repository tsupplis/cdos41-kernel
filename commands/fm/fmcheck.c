/* Noninteractive regression executable. This is not the replacement FM. */
#include "fm.h"
#include "menu.h"
#ifdef HOST_TEST
#include <stdio.h>
#else
int printf();
#endif
int failures;
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
    char *p, *before;
    unsigned value;
    int i;
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
