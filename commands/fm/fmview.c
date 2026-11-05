/* Experimental FM reconstruction. Not the distributed FM replacement.
 * Current drive, FAT directories and CP/M users; Escape exits/backtracks.
 * Drive Copy, Rename and Delete are enabled; external launching is pending.
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
#include "deljob.h"
#include "delio.h"
#include "copyjob.h"
#include "copyio.h"
#include "copynam.h"
#include "fatdest.h"
#include "book.h"
static struct fm_book bookmarks[2];
static char book_message[80];
static char current_directory[]=".           ";
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
static int copy_menu,copy_choosing,copy_user_choosing,copy_target_user;
static char copy_message[80];
static struct fm_navigation copy_navigation;
static char *copy_labels[]={"Help","Copy to A:","Copy to B:","Copy to C:",
    "Copy to D:","Copy to Drive","Copy to Dir #1","Copy to Dir #2",
    "Copy to Dir","Copy to New Name"};
static int copy_destination();
static int picker_cancel();
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
    if(copy_menu) {
        if(layout.menu.height>=3) fm_frame(&canvas,&layout.menu,1,menuattr);
        for(i=0;i<copy_navigation.capacity;++i) {
            int entry;
            entry=copy_navigation.offset+i;
            if(entry>=copy_navigation.count) break;
            text(layout.menu.row+(layout.menu.height>=3 ? 1 : 0)+i,
                 layout.menu.column+(layout.menu.height>=3 ? 1 : 0),
                 copy_labels[entry],layout.menu.width-(layout.menu.height>=3 ? 2 : 0),
                 entry+1==copy_navigation.selected ? menu_selected : menuattr);
        }
    } else if(layout.menu.height>=3) {
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
         notice ? notice : copy_menu ?
         ">>>  CHOOSE A DESTINATION FOR THE FILES SHOWN BELOW  >>>>" :
         copy_user_choosing ? "select destination directory" :
         copy_choosing ? "Copy to Drive: Enter selects; Escape cancels" : focus.active ? fm_menu_items[fm_focus_index(&focus)].description :
         drives ? "Drives: Enter selects; Escape returns" :
         directories ? "Directories: F3/F4 set Dir #1/#2; Enter selects; Escape returns" :
         "FMVIEW: Tab menu; F9 directories; arrows move; Escape exits",
         layout.prompt.width,promptattr);
    if(layout.prompt.row+layout.prompt.height<24)
        text(23,0,"Prototype: external launching is disabled",80,keyattr);
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
        if(directories && fat) {
            for(i=0;i<total;++i) if(names[i][0]=='.' && names[i][1]==' ') break;
            if(i==total && total<256) names[total++]=current_directory;
        }
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
        if(names[selected]==current_directory) {
            directories=0;notice=0;fm_marks_clear(&marks);return refresh();
        }
        for(i=0;i<count;++i) if(names[selected]==files[i].name) break;
        if(i==count || !fm_native_enter(drive,files[i].raw)) {
            notice="Cannot enter directory";return 1;
        }
        /* Only an already-owned unpinned working alias can be refreshed. */
        if(drive>=14) fm_fat_refresh_owned(drive);
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
    if(drive>=14 && fm_fat_valid(drive)) available|=(unsigned)1<<(drive-1);
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
static int select_drive(next)
int next;
{
    if(next>=14 && next<=16 && fm_fat_valid(next)) {
        if((__BDOS(14,next-1)&255)==255) return 0;
        return (__BDOS(25,0)&255)==next-1;
    }
    return fm_native_drive(next);
}
static int drive_select()
{
    int next;
    if(!browser.navigation.selected) return 1;
    next=drive_numbers[browser.navigation.selected-1];
    if(copy_choosing) {
        copy_choosing=0;
        if(!picker_cancel()) return 0;
        return copy_destination(next);
    }
    if(!select_drive(next)) {notice="Cannot select drive";return 1;}
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
/* Rename and named Copy share editing; limits and headings follow each
 * original dialog. No console lock is held while waiting for a key. */
static int name_ask(prefix,name,target,limit)
char *prefix,*name,*target;
int limit;
{
    char heading[40];
    int i,j,key,ok,length;
    i=0;
    while(*prefix) heading[i++]=*prefix++;
    for(j=0;j<12 && name[j] && name[j]!=' ';++j) heading[i++]=name[j];
    heading[i++]=' ';heading[i++]='t';heading[i++]='o';
    heading[i++]=' ';heading[i++]='?';heading[i++]=' ';heading[i]=0;
    length=0;target[0]=0;
    do {
        if(!fm_console_begin(&console)) return -2;
        ok=text(21,0,heading,i,promptattr);
        if(ok) ok=text(21,i,target,80-i,promptattr);
        if(!fm_console_end(&console) || !ok) return -2;
        do {
            key=fm_console_key(&console,0,0,0);
            if(key==-1) __BDOS(142,0);
        } while(key==-1);
        if(key<0) return -2;
        if(key==27) return -1;
        if(key==13) return length ? 1 : 0;
        if(key>= 'a' && key<= 'z') key-=32;
        if(key==24) length=0;
        else if(key==8 || key==127) {if(length) --length;}
        else if(key<32) return 0;
        else if(key<=126 && length<limit) target[length++]=key;
        target[length]=0;
    } while(1);
}
static int rename_ask(name,target)
char *name,*target;
{ return name_ask("Rename, ",name,target,12); }
static int copy_name_ask(name,target)
char *name,*target;
{ return name_ask("Copy ",name,target,15); }
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
static int delete_confirm()
{
    int answer,key,ok;
    char reply[2];
    answer=0;
    do {
        reply[0]=answer;reply[1]=0;
        if(!fm_console_begin(&console)) return -1;
        ok=text(21,0,"ERASE, are you sure (Y=yes) ? ",30,promptattr);
        if(ok) ok=text(21,30,reply,50,promptattr);
        if(!fm_console_end(&console) || !ok) return -1;
        do {
            key=fm_console_key(&console,0,0,0);
            if(key==-1) __BDOS(142,0);
        } while(key==-1);
        if(key<0) return -1;
        if(key==13) return answer=='Y';
        if(key==8 || key==127 || key==24) answer=0;
        else if(key<32) return 0;
        else if(!answer && key<=126) {
            answer=key;
            if(answer>='a' && answer<='z') answer-=32;
        }
    } while(1);
}
static int delete_action()
{
    struct fm_eraser ops;
    int result;
    if(directories || drives || !browser.navigation.count) {
        notice="Select files to erase";return 1;
    }
    focus.active=0;ops.confirm=delete_confirm;ops.erase=fm_delete_file;
    result=fm_delete_files(&browser,files,count,&marks,drive,&ops);
    if(!result) return 0;
    if(result==2) return 1;
    if(!refresh_retained()) return 0;
    notice=marks.count ? "NOT ERASED" : 0;
    return 1;
}
static int copy_cancel()
{
    int key;
    key=fm_console_key(&console,0,0,0);
    return key==-1 ? 0 : 1;
}
static int copy_notice(name)
char *name;
{
    int ok;
    if(!fm_console_begin(&console)) return 0;
    ok=text(21,0,"Press ANY KEY to stop copy",80,promptattr);
    if(ok) ok=text(23,0,name,80,keyattr);
    if(!fm_console_end(&console)) ok=0;
    return ok;
}
static int copy_status(result,destination,destuser)
int result,destination,destuser;
{
    int i;
    char *recovery,*out;
    notice=result==1 ? "Copy done" : result==0 ? "Copy aborted" : "NOT COPIED";
    recovery=fm_copy_recovery();
    if(*recovery) {
        out=copy_message;
        notice="Copy failed; retained ";
        while(*notice) *out++=*notice++;
        *out++='A'+destination-1;*out++=':';
        for(i=0;recovery[i] && i<12;++i) *out++=recovery[i];
        if(destuser!=user) {
            *out++=' ';*out++='(';*out++='u';*out++='s';*out++='e';*out++='r';
            *out++=' ';*out++='0'+destuser/10;*out++='0'+destuser%10;*out++=')';
        }
        *out=0;notice=copy_message;
    }
    return 1;
}
static int copy_destination(destination)
int destination;
{
    struct fm_copier ops;
    int result,same;
    same=destination==drive;
    if(fat && fm_fat_valid(destination)) {
        same=fm_fat_same(drive,destination);
        if(*fm_fat_destination_error()) {notice=fm_fat_destination_error();return 1;}
    }
    if(same) {
        notice="Destination must be different than source";return 1;
    }
    if(!(fm_native_drives()&((unsigned)1<<(destination-1))) && !fm_fat_valid(destination)) {
        notice="Drive not configured";return 1;
    }
    copy_menu=copy_choosing=focus.active=0;
    fm_copy_reset();
    ops.transfer=fm_copy_file;ops.cancel=copy_cancel;ops.notice=copy_notice;
    result=fm_copy_files(&browser,files,count,&marks,drive,destination,dma,&ops);
    return copy_status(result,destination,user);
}
static int copy_named_action()
{
    struct fm_named_copier ops;
    int result;
    copy_menu=copy_choosing=focus.active=0;
    fm_copy_reset();
    ops.ask=copy_name_ask;ops.transfer=fm_copy_named;
    ops.cancel=copy_cancel;ops.report=rename_report;
    result=fm_copy_names(&browser,files,count,&marks,drive,dma,&ops);
    if(!refresh_retained()) return 0;
    return copy_status(result,fm_copy_name_drive(),user);
}
/* User areas are independent CP/M directories. The engine switches user
 * around each source/destination operation and restores the caller's user. */
static int copy_user_transfer(sd,raw,dd,restore,cancel)
int sd,dd;
char *raw,*restore;
int (*cancel)();
{
    return fm_copy_users(sd,user,raw,dd,copy_target_user,raw,restore,cancel);
}
/* Use the same synthetic current-directory entry in both directory views. */
static int selected_directory(raw)
char *raw;
{
    int i,j;
    if(!browser.navigation.selected) return 0;
    j=browser.navigation.selected-1;
    if(names[j]==current_directory) {
        for(i=0;i<32;++i) raw[i]=0;
        for(i=1;i<12;++i) raw[i]=' ';
        raw[1]='.';raw[16]=64;return 1;
    }
    for(i=0;i<count;++i) if(names[j]==files[i].name) break;
    if(i==count || !files[i].directory) return 0;
    for(j=0;j<32;++j) raw[j]=files[i].raw[j];
    return 1;
}
static int book_set(slot)
int slot;
{
    char raw[32],label[32],*p;
    int i,j,targetuser;
    if(!directories || drives || copy_user_choosing || copy_choosing || copy_menu)
        return 1;
    if(!browser.navigation.selected) return 1;
    targetuser=user;
    if(fat) {if(!selected_directory(raw)) return 1;}
    else targetuser=browser.navigation.selected-1;
    label[0]='A'+drive-1;label[1]=':';i=2;
    p=names[browser.navigation.selected-1];
    for(j=0;j<12 && p[j];++j) label[i++]=p[j];
    while(i>2 && label[i-1]==' ') --i;
    label[i]=0;
    if(!fm_book_set(&bookmarks[slot],fat,drive,targetuser,raw,label,dma)) {
        notice=fat ? fm_fat_destination_error() : "Cannot set directory bookmark";
        return 1;
    }
    p="DIR #1 set to: ";i=0;
    while(*p) book_message[i++]=*p++;
    book_message[5]='1'+slot;
    for(j=0;bookmarks[slot].label[j];++j) book_message[i++]=bookmarks[slot].label[j];
    book_message[i]=0;notice=book_message;
    return 1;
}
static int book_unset(slot)
int slot;
{
    notice=slot ? "first set Dir #2" : "first set Dir #1";return 1;
}
static int book_go(slot)
int slot;
{
    int next;
    if(!bookmarks[slot].set) return book_unset(slot);
    next=fm_book_target(&bookmarks[slot],1,dma);
    if(!next || !select_drive(next)) {
        notice="Cannot select saved directory";return 1;
    }
    drive=next;user=bookmarks[slot].user;fat=bookmarks[slot].fat;
    __BDOS(32,user);
    directories=drives=focus.active=0;notice=0;
    fm_marks_clear(&marks);
    return refresh();
}
static int copy_book(slot)
int slot;
{
    struct fm_copier ops;
    int destination,result,same;
    if(!bookmarks[slot].set) return book_unset(slot);
    destination=fm_book_target(&bookmarks[slot],0,dma);
    if(!destination) {notice="Cannot select saved directory";return 1;}
    same=destination==drive && bookmarks[slot].user==user;
    if(bookmarks[slot].fat) {
        same=fm_fat_same(drive,destination);
        if(*fm_fat_destination_error()) {notice=fm_fat_destination_error();return 1;}
    }
    if(same) {
        notice="Destination must be different than source";return 1;
    }
    copy_menu=copy_choosing=focus.active=0;
    fm_copy_reset();
    ops.cancel=copy_cancel;ops.notice=copy_notice;
    copy_target_user=bookmarks[slot].user;
    if(bookmarks[slot].fat) {
        ops.transfer=fm_copy_file;
        result=fm_copy_files(&browser,files,count,&marks,drive,destination,dma,&ops);
    } else {
        ops.transfer=copy_user_transfer;
        result=fm_copy_batch(&browser,files,count,&marks,drive,destination,dma,&ops);
    }
    return copy_status(result,destination,copy_target_user);
}
static int copy_user_select()
{
    struct fm_copier ops;
    int result,alias;
    char raw[32];
    if(!browser.navigation.selected) return 1;
    if(fat) {
        if(!selected_directory(raw)) return 0;
        alias=fm_fat_destination(drive,raw,dma);
        if(alias<=0) {
            notice=alias<0 ? "Destination must be different than source" : fm_fat_destination_error();
            return 1;
        }
        copy_user_choosing=0;
        if(!picker_cancel()) return 0;
        fm_copy_reset();
        ops.transfer=fm_copy_file;ops.cancel=copy_cancel;ops.notice=copy_notice;
        result=fm_copy_files(&browser,files,count,&marks,drive,alias,dma,&ops);
        return copy_status(result,alias,user);
    }
    copy_target_user=browser.navigation.selected-1;
    if(copy_target_user==user) {
        notice="Destination must be different than source";return 1;
    }
    copy_user_choosing=0;
    if(!picker_cancel()) return 0;
    fm_copy_reset();
    ops.transfer=copy_user_transfer;ops.cancel=copy_cancel;ops.notice=copy_notice;
    result=fm_copy_batch(&browser,files,count,&marks,drive,drive,dma,&ops);
    return copy_status(result,drive,copy_target_user);
}
static int copy_action()
{
    if(directories || drives || !browser.navigation.count) {
        notice="Select files to copy";return 1;
    }
    copy_menu=1;copy_navigation.count=10;copy_navigation.selected=1;
    copy_navigation.offset=0;copy_navigation.columns=1;
    copy_navigation.capacity=layout.menu.height>=3 ? layout.menu.height-2 : 1;
    return 1;
}
static int copy_key(key)
int key;
{
    int entry;
    if(key==27) {copy_menu=0;focus.active=0;return 1;}
    if(key==0xc1 || key==0xc2) return copy_book(key-0xc1);
    if(key>=0xbd && key<=0xc0) return copy_destination(key-0xbc);
    if(key!=13) {fm_navigate(&copy_navigation,key);return 1;}
    entry=copy_navigation.selected-1;
    if(entry>=1 && entry<=4) return copy_destination(entry);
    if(entry==6 || entry==7) return copy_book(entry-6);
    if(entry==9) return copy_named_action();
    if(entry==8) {
        copy_menu=0;copy_user_choosing=1;return directory_view();
    }
    if(entry==5) {
        copy_menu=0;copy_choosing=1;return drive_view();
    }
    notice="This destination is not yet implemented";
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
    /* Return BDOS file errors to this process instead of aborting the UI. */
    __BDOS(45,255);
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
                if(copy_menu) result=copy_key(key) ? 1 : -1;
                else if(copy_user_choosing && key==27) {
                    copy_user_choosing=0;result=picker_cancel() ? 1 : -1;
                }
                else if(copy_user_choosing && key==13) result=copy_user_select() ? 1 : -1;
                else if(copy_user_choosing) result=fm_browser_key(&browser,key)>0 ? 1 : 0;
                else if(copy_choosing && key==27) {copy_choosing=0;result=picker_cancel() ? 1 : -1;}
                else if(copy_choosing && key==13) result=drive_select() ? 1 : -1;
                else if(copy_choosing) result=fm_browser_key(&browser,key)>0 ? 1 : 0;
                else if(input.active) result=subset_key(key) ? 1 : -1;
                else if((key==0xbd || key==0xbe) && directories && !drives)
                    result=book_set(key-0xbd) ? 1 : -1;
                else if(key==0xc1 || key==0xc2) result=book_go(key-0xc1) ? 1 : -1;
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
                        else if(fm_focus_index(&focus)==6) result=copy_action();
                        else if(fm_focus_index(&focus)==7) result=rename_action() ? 1 : -1;
                        else if(fm_focus_index(&focus)==8) result=delete_action() ? 1 : -1;
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
