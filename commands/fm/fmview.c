/* Experimental read-only FM browser. Not the distributed FM replacement.
 * Current drive, FAT directories and CP/M users; Escape exits/backtracks.
 * Only directory/setup selection is active. No copy, rename, delete or launch.
 */
#include "fm.h"
#include "event.h"
#include "scan.h"
#include "menu.h"
#include "term.h"
#include "focus.h"
int printf();
static struct fm_file files[256];
static char *names[256];
static char usernames[16][13];
static int drive,user,fat,count,directories,saved_selection,saved_offset;
static char *notice;
static char dma[128], fcb[36];
static struct fm_canvas canvas;
static struct fm_console console;
static struct fm_browser browser;
static struct fm_layout layout;
static struct fm_config config;
static struct fm_focus focus;
static int menu_selected;
static int normal, menuattr, promptattr, keyattr, limited;
static int text(row,column,string,width,attr)
int row,column,width,attr;
char *string;
{
    int i,ch;
    for(i=0;i<width;++i) {
        ch=*string ? *string++ : ' ';
        if(!(*canvas.cell)(row,column+i,ch,attr)) return 0;
    }
    return 1;
}
static int decoration()
{
    int row,column,i;
    if(!fm_console_begin(&console)) return 0;
    for(row=0;row<24;++row)
        for(column=0;column<80;++column)
            (*canvas.cell)(row,column,' ',normal);
    if(layout.menu.height>=3) {
        fm_frame(&canvas,&layout.menu,1,menuattr);
        for(i=0;i<focus.navigation.capacity;++i) {
            int entry,attr;
            entry=focus.navigation.offset+i;
            if(entry>=focus.navigation.count) break;
            attr=focus.active && entry+1==focus.navigation.selected ? menu_selected : menuattr;
            text(layout.menu.row+1+i,layout.menu.column+1,
                 fm_menu_items[(focus.setup ? fm_file_menu_count : 0)+entry].label,
                 layout.menu.width-2,attr);
        }
    } else {
        text(layout.menu.row,layout.menu.column,
             fm_menu_items[fm_focus_index(&focus)].label,layout.menu.width,
             focus.active ? menu_selected : menuattr);
    }
    text(layout.prompt.row,layout.prompt.column,
         notice ? notice : focus.active ? fm_menu_items[fm_focus_index(&focus)].description :
         directories ? "Directories: Enter selects; Escape returns" :
         "FMVIEW: Tab menu; F9 directories; arrows move; Escape exits",
         layout.prompt.width,promptattr);
    if(layout.prompt.row+layout.prompt.height<24)
        text(23,0,"Read-only prototype: copy, rename, delete and launch are disabled",80,keyattr);
    if(limited) text(layout.prompt.row,layout.prompt.column,
         "Directory list truncated at 256 entries",layout.prompt.width,promptattr);
    return fm_console_end(&console);
}
static int fatmedia()
{
    int i;
    for(i=0;i<36;++i) fcb[i]=0;
    for(i=1;i<12;++i) fcb[i]=' ';
    for(i=0;i<128;++i) dma[i]=0;
    fcb[0]='?';
    __BDOS(26,dma); __BDOS(17,fcb);
    return (dma[0]&255)==32 && (dma[15]&255)==128;
}
/* Retain separate sorted lists, as the original does. The first directory
 * view is deliberately limited to the current drive, not drive selection.
 */
static int refresh()
{
    int i,j,result,total;
    result=fm_native_scan(drive,user,fat,files,256,&count,dma);
    if(result<0) return 0;
    limited=result==0;total=0;
    if(directories && !fat) {
        for(i=0;i<16;++i) {
            for(j=0;j<12;++j) usernames[i][j]=' ';
            usernames[i][0]='U';usernames[i][1]='s';usernames[i][2]='e';
            usernames[i][3]='r';usernames[i][5]='0'+i/10;
            usernames[i][6]='0'+i%10;usernames[i][12]=0;
            names[total++]=usernames[i];
        }
    } else {
        for(i=0;i<count;++i)
            if(files[i].directory==directories) names[total++]=files[i].name;
        fm_directory_sort(names,total);
    }
    return fm_browser_open(&browser,names,total,&layout.files,14,normal,
                    fm_attribute(config.value[2],config.value[3],1));
}
static int directory_view()
{
    if(!directories) {
        saved_selection=browser.navigation.selected;
        saved_offset=browser.navigation.offset;
    }
    directories=1;focus.active=0;notice=0;
    return refresh();
}
static int directory_select()
{
    int i,selected;
    if(!browser.navigation.selected) return 1;
    selected=browser.navigation.selected-1;
    if(fat) {
        for(i=0;i<count;++i) if(names[selected]==files[i].name) break;
        if(i==count || !fm_native_enter(drive,files[i].raw)) {
            notice="Cannot enter directory";return 1;
        }
    } else {
        user=selected;
        __BDOS(32,user);
    }
    directories=0;notice=0;
    return refresh();
}
main(argc,argv)
int argc;
char **argv;
{
    int i,result,key,action,original_user;
    if(argc!=1) { printf("USAGE: FMVIEW\n"); return 1; }
    drive=(__BDOS(25,0)&255)+1;user=__BDOS(32,255)&255;original_user=user;
    fm_config_defaults(&config);
    if(fm_config_load(&config,dma)<0) {
        printf("FMVIEW: configuration read failed\n");return 1;
    }
    for(i=2;i<8;++i) if((config.value[i]&255)>15) break;
    if(i<8 || (config.value[14]&255)>15 || (config.value[15]&255)>15) {
        printf("FMVIEW: invalid configuration colour\n");return 1;
    }
    if(!fm_layout_calculate(&layout,&config,24,80,0)) {
        printf("FMVIEW: invalid configuration geometry\n");return 1;
    }
    fat=fatmedia();
    normal=fm_attribute(config.value[2],config.value[3],0);
    menuattr=fm_attribute(config.value[4],config.value[5],0);
    promptattr=fm_attribute(config.value[6],config.value[7],0);
    keyattr=fm_attribute(config.value[14],config.value[15],0);
    menu_selected=fm_attribute(config.value[4],config.value[5],1);
    fm_focus_open(&focus,layout.menu.height>2 ? layout.menu.height-2 : 1);
    if(!refresh()) { printf("FMVIEW: directory search failed\n");return 1; }
    if(!fm_term_open(&canvas,&console)) {
        printf("FMVIEW: CDOS 4.1 PC window console required\n");return 1;
    }
    __BDOS(6,27);__BDOS(6,'f');
    if(!decoration() || !fm_browser_paint(&browser,&canvas,&console)) result=-1;
    else {
        do {
            key=fm_console_key(&console,0,0,0);
            if(key==-1) {result=0;__BDOS(142,0);}
            else if(key<0) result=-1;
            else {
                notice=0;
                if(key==0xc3) result=directory_view() ? 1 : -1;
                else {
                    action=fm_focus_key(&focus,key);
                    if(action==2) {
                        if(fm_focus_index(&focus)==1) result=directory_view() ? 1 : -1;
                        else {notice="This action is not yet implemented";result=1;}
                    } else if(action<0) {
                        if(key==27 && directories) {
                            directories=0;result=refresh() ? 1 : -1;
                            if(result==1 && saved_selection<=browser.navigation.count) {
                                browser.navigation.selected=saved_selection;
                                browser.navigation.offset=saved_offset;
                            }
                        } else if(key==27) result=2;
                        else if(key==13 && directories) result=directory_select() ? 1 : -1;
                        else result=fm_browser_key(&browser,key)>0 ? 1 : 0;
                    } else result=action ? 1 : 0;
                }
                if(result==1) {
                    if(!decoration() || !fm_browser_paint(&browser,&canvas,&console))
                        result=-1;
                }
            }
        } while(result>=0 && result!=2);
    }
    fm_term_close(&console);
    __BDOS(32,original_user);
    __BDOS(6,27);__BDOS(6,'e');
    __BDOS(6,27);__BDOS(6,'E');
    printf("FMVIEW: %s\n",result<0 ? "console error" : "closed");
    return result<0;
}
