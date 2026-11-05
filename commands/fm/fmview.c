/* Experimental FM reconstruction. Not the distributed FM replacement.
 * Current drive, FAT directories and CP/M users; Escape exits/backtracks.
 * Rename is enabled; copy, delete and external launching remain disabled.
 */
#include "fm.h"
#include "event.h"
#include "scan.h"
#include "menu.h"
#include "term.h"
#include "focus.h"
#include "select.h"
#include "marks.h"
#include "viewer.h"
#include "printjob.h"
#include "renjob.h"
#include "renio.h"
int printf();
static struct fm_file files[256];
static char *names[256];
static char usernames[16][13],drivenames[16][13];
static int drive_numbers[16],drive_count,drives;
static char masks[16][11];
static struct fm_input input;
static struct fm_marks marks;
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
         drives ? "Drives: Enter selects; Escape returns" :
         directories ? "Directories: Enter selects; Escape returns" :
         "FMVIEW: Tab menu; F9 directories; arrows move; Escape exits",
         layout.prompt.width,promptattr);
    if(layout.prompt.row+layout.prompt.height<24)
        text(23,0,"Prototype: copy, delete and launch are disabled",80,keyattr);
    if(input.active) {
        text(layout.prompt.row,layout.prompt.column,"Subset: ",8,promptattr);
        text(layout.prompt.row,layout.prompt.column+8,input.text,
             layout.prompt.width>8 ? layout.prompt.width-8 : 0,promptattr);
    }
    if(limited && !input.active) text(layout.prompt.row,layout.prompt.column,
         "Directory list truncated at 256 entries",layout.prompt.width,promptattr);
    return fm_console_end(&console);
}
static int repaint()
{
    int ok;
    if(!decoration() || !fm_console_begin(&console)) return 0;
    ok=fm_browser_draw(&browser,&canvas);
    if(ok && !directories && !drives) ok=fm_marks_draw(&marks,&browser,&canvas);
    if(!fm_console_end(&console)) ok=0;
    return ok;
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
/* Rebuild the current view. Picker navigation preserves file marks; only
 * accepting a new directory, drive or subset clears them. */
static int refresh()
{
    int i,j,result,total;
    if(drives) {
        for(i=0;i<drive_count;++i) names[i]=drivenames[i];
        total=drive_count;limited=0;
        return fm_browser_open(&browser,names,total,&layout.files,14,normal,
                        fm_attribute(config.value[2],config.value[3],1));
    }
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
            if(files[i].directory==directories &&
               (directories || fm_subset_match(masks[drive-1],files[i].raw)))
                names[total++]=files[i].name;
        fm_directory_sort(names,total);
    }
    return fm_browser_open(&browser,names,total,&layout.files,14,normal,
                    fm_attribute(config.value[2],config.value[3],1));
}
static int directory_view()
{
    if(!directories && !drives) {
        saved_selection=browser.navigation.selected;
        saved_offset=browser.navigation.offset;
    }
    directories=1;drives=0;focus.active=0;notice=0;
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
    fm_marks_clear(&marks);
    return refresh();
}
static int drive_view()
{
    unsigned available;
    int i,j;
    available=fm_native_drives();drive_count=0;
    for(i=0;i<16;++i) if(available&((unsigned)1<<i)) {
        drive_numbers[drive_count]=i+1;
        for(j=0;j<12;++j) drivenames[drive_count][j]=' ';
        drivenames[drive_count][0]='A'+i;drivenames[drive_count][1]=':';
        drivenames[drive_count][12]=0;++drive_count;
    }
    if(!drive_count) {notice="No configured drives found";return 1;}
    if(!directories && !drives) {
        saved_selection=browser.navigation.selected;
        saved_offset=browser.navigation.offset;
    }
    drives=1;directories=0;focus.active=0;return refresh();
}
static int drive_select()
{
    int next;
    if(!browser.navigation.selected) return 1;
    next=drive_numbers[browser.navigation.selected-1];
    if(!fm_native_drive(next)) {notice="Cannot select drive";return 1;}
    drive=next;fat=fatmedia();drives=directories=0;
    fm_marks_clear(&marks);
    return refresh();
}
/* Picker-to-picker transitions retain the original file view checkpoint. */
static int picker_cancel()
{
    directories=drives=0;
    if(!refresh()) return 0;
    if(saved_selection>=1 && saved_selection<=browser.navigation.count) {
        browser.navigation.selected=saved_selection;
        browser.navigation.offset=saved_offset;
    }
    return 1;
}
static int subset_key(key)
int key;
{
    int action;
    action=fm_input_key(&input,key);
    if(action==2) {
        if(!fm_native_subset(input.text,masks[drive-1])) {
            notice="Include ? or *, 12 characters max.";
            input.active=0;return 1;
        }
        input.active=0;focus.active=0;directories=drives=0;
        fm_marks_clear(&marks);
        return refresh();
    }
    return 1;
}
/* Keep failed/skipped file identities across the post-rename rescan. */
static char retained[256][13];
static int refresh_retained()
{
    int i,j,k,n;
    n=0;
    for(i=0;i<browser.navigation.count;++i) if(marks.value[i]) {
        for(j=0;j<13;++j) retained[n][j]=names[i][j];
        ++n;
    }
    if(!refresh()) return 0;
    fm_marks_clear(&marks);
    for(i=0;i<browser.navigation.count;++i) for(j=0;j<n;++j) {
        for(k=0;k<12 && names[i][k]==retained[j][k];++k) ;
        if(k==12) fm_marks_key(&marks,i+1,browser.navigation.count,44);
    }
    for(i=0;i<browser.navigation.count;++i) if(marks.value[i]) {
        /* Use navigation itself to restore a visible first retained file. */
        while(browser.navigation.selected<i+1) fm_browser_key(&browser,12);
        break;
    }
    return 1;
}
static int rename_report(message)
char *message;
{
    int ok;
    if(!fm_console_begin(&console)) return 0;
    ok=text(22,0,message,80,promptattr);
    if(!fm_console_end(&console)) ok=0;
    return ok;
}
static int rename_ask(name,target)
char *name,*target;
{
    struct fm_input edit;
    char heading[40];
    int i,j,key,action,ok;
    i=0;heading[i++]='R';heading[i++]='e';heading[i++]='n';
    heading[i++]='a';heading[i++]='m';heading[i++]='e';
    heading[i++]=',';heading[i++]=' ';
    for(j=0;j<12 && name[j] && name[j]!=' ';++j) heading[i++]=name[j];
    heading[i++]=' ';heading[i++]='t';heading[i++]='o';
    heading[i++]=' ';heading[i++]='?';heading[i++]=' ';heading[i]=0;
    fm_input_open(&edit);action=0;
    do {
        if(!fm_console_begin(&console)) return -2;
        ok=text(21,0,heading,i,promptattr);
        if(ok) ok=text(21,i,edit.text,80-i,promptattr);
        if(!fm_console_end(&console) || !ok) return -2;
        do {
            key=fm_console_key(&console,0,0,0);
            if(key==-1) __BDOS(142,0);
        } while(key==-1);
        if(key<0) return -2;
        if(key>= 'a' && key<= 'z') key-=32;
        if(key==24) {fm_input_open(&edit);action=0;continue;}
        if(key<32 && key!=8 && key!=13 && key!=27) return 0;
        action=fm_input_key(&edit,key);
        if(action<0) return -1;
    } while(action!=2);
    for(j=0;j<=edit.length;++j) target[j]=edit.text[j];
    return edit.length ? 1 : 0;
}
static int rename_action()
{
    struct fm_renamer ops;
    int result;
    if(directories || drives || !browser.navigation.count) {
        notice="Select files to rename";return 1;
    }
    focus.active=0;
    ops.ask=rename_ask;ops.change=fm_rename_file;ops.report=rename_report;
    result=fm_rename_files(&browser,files,count,&marks,drive,dma,&ops);
    if(!result || !refresh_retained()) return 0;
    notice=marks.count ? "NOT RENAMED" : 0;
    return 1;
}
static int print_notice(name)
char *name;
{
    int ok;
    if(!fm_console_begin(&console)) return 0;
    ok=text(layout.prompt.row,layout.prompt.column,
            "Press ANY KEY to stop printing",layout.prompt.width,promptattr);
    if(ok) ok=text(23,0,"Printing, ",10,keyattr);
    if(ok) ok=text(23,10,name,70,keyattr);
    if(!fm_console_end(&console)) ok=0;
    return ok;
}
static int print_action()
{
    struct fm_printer printer;
    int result;
    if(directories || drives || !browser.navigation.count) {
        notice="Select files to print";return 1;
    }
    focus.active=0;
    fm_printer_native(&printer,print_notice);
    result=fm_print_files(&browser,files,count,&marks,drive,dma,&printer);
    notice=result==0 ? "Printer not available" :
           result<0 ? "NOT PRINTED: file or printer error" :
           marks.count ? "NOT PRINTED" : 0;
    return 1;
}
static int type_action()
{
    int result;
    if(directories || drives || !browser.navigation.count) {
        notice="Select files to type";return 1;
    }
    focus.active=0;
    result=fm_view_files(&browser,files,count,&marks,drive,dma,
                         &canvas,&console,normal);
    if(result<0) {notice="NOT typed: file read/open/close error";return 1;}
    return result;
}
main(argc,argv)
int argc;
char **argv;
{
    int i,j,result,key,action,original_user,original_drive;
    if(argc!=1) { printf("USAGE: FMVIEW\n"); return 1; }
    drive=(__BDOS(25,0)&255)+1;user=__BDOS(32,255)&255;original_user=user;original_drive=drive;
    for(i=0;i<16;++i) for(j=0;j<11;++j) masks[i][j]='?';
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
    if(!repaint()) result=-1;
    else {
        do {
            key=fm_console_key(&console,0,0,0);
            if(key==-1) {result=0;__BDOS(142,0);}
            else if(key<0) result=-1;
            else {
                notice=0;
                if(input.active) result=subset_key(key) ? 1 : -1;
                else if(key==0xbc || key==2) result=type_action() ? 1 : -1;
                else if(key==0xc3) result=directory_view() ? 1 : -1;
                else {
                    action=fm_focus_key(&focus,key);
                    if(action==2) {
                        if(fm_focus_index(&focus)==1) result=directory_view() ? 1 : -1;
                        else if(fm_focus_index(&focus)==2) {fm_input_open(&input);result=1;}
                        else if(fm_focus_index(&focus)==3) result=drive_view() ? 1 : -1;
                        else if(fm_focus_index(&focus)==4) result=type_action() ? 1 : -1;
                        else if(fm_focus_index(&focus)==5) result=print_action();
                        else if(fm_focus_index(&focus)==7) result=rename_action() ? 1 : -1;
                        else {notice="This action is not yet implemented";result=1;}
                    } else if(action<0) {
                        if(key==27 && (directories || drives)) {
                            result=picker_cancel() ? 1 : -1;
                        } else if(key==27) result=2;
                        else if(key==13 && drives) result=drive_select() ? 1 : -1;
                        else if(key==13 && directories) result=directory_select() ? 1 : -1;
                        else {
                            action=(!directories && !drives) ?
                                fm_marks_key(&marks,browser.navigation.selected,
                                             browser.navigation.count,key) : -1;
                            if(action>=0) result=action;
                            else result=fm_browser_key(&browser,key)>0 ? 1 : 0;
                        }
                    } else result=action ? 1 : 0;
                }
                if(result==1) {
                    if(!repaint())
                        result=-1;
                }
            }
        } while(result>=0 && result!=2);
    }
    fm_term_close(&console);
    __BDOS(14,original_drive-1);
    __BDOS(32,original_user);
    __BDOS(6,27);__BDOS(6,'e');
    __BDOS(6,27);__BDOS(6,'E');
    printf("FMVIEW: %s\n",result<0 ? "console error" : "closed");
    return result<0;
}
