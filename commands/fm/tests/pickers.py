"""Exercise the real FMVIEW controller with a deterministic read-only disk adapter."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
source=r"""
#include <assert.h>
#include <string.h>
int __BDOS();
int sprintf();
#define main fmview_main
#include "fmview.c"
#undef main
static int native_drive=1,capture_result=14,clone_result=16,pins[17],valid_alias=1;
static int captures,clones,same_location,location_error,copy_calls,batch_calls,lastdest,lastuser;
int __BDOS(fn,arg)
int fn,arg;
{if(fn==14)native_drive=arg+1;return fn==25 ? native_drive-1 : 0;}
int fm_view_files(){return 1;}
int fm_print_files(){return 1;}
int fm_rename_file(){return 1;}
int fm_rename_files(){return 1;}
int fm_delete_file(){return 1;}
int fm_delete_files(){return 1;}
int fm_copy_file(){return 1;}
int fm_copy_named(){return 1;}
int fm_copy_names(){return 1;}
int fm_copy_name_drive(){return 1;}
char *fm_copy_recovery(){return "";}
int fm_copy_reset(){return 0;}
int fm_copy_files(b,f,n,m,sd,dd,d,ops)
struct fm_browser *b;struct fm_file *f;int n,sd,dd;struct fm_marks *m;
char *d;struct fm_copier *ops;
{++copy_calls;lastdest=dd;return 1;}
int fm_copy_batch(b,f,n,m,sd,dd,d,ops)
struct fm_browser *b;struct fm_file *f;int n,sd,dd;struct fm_marks *m;
char *d;struct fm_copier *ops;
{++batch_calls;lastdest=dd;lastuser=copy_target_user;return 1;}
int fm_copy_users(){return 1;}
int fm_fat_destination(){return 14;}
int fm_fat_capture(){++captures;return capture_result;}
int fm_fat_clone(){++clones;return clone_result;}
int fm_fat_refresh_owned(){return 1;}
int fm_fat_pin(d) int d; {++pins[d];return 1;}
int fm_fat_unpin(d) int d; {--pins[d];return 1;}
int fm_fat_valid(d) int d; {return d>=14 && valid_alias;}
int fm_fat_same(){return same_location;}
char *fm_fat_destination_error(){return location_error ? "error" : "";}
int fm_printer_native(){return 1;}
int fm_config_load(){return 0;}
int fm_term_open(){return 0;}
int fm_term_close(){return 0;}
int fm_native_enter(){return 1;}
unsigned fm_native_drives(){return 3;}
int fm_native_drive(){return 1;}
int fm_native_subset(){return 1;}
int fm_native_scan(d,u,f,out,cap,n,dma)
int d,u,f,cap,*n;struct fm_file *out;char *dma;
{
 int i;
 for(i=0;i<120;++i) {
  sprintf(out[i].name,"F%07d.TXT",i);
  memset(out[i].raw,' ',32);out[i].directory=0;
 }
 *n=120;return 1;
}
int main(void)
{
 int i,j;
 fm_config_defaults(&config);
 assert(fm_layout_calculate(&layout,&config,24,80,0));
 fm_focus_open(&focus,18);drive=1;fat=1;
 for(i=0;i<16;++i)for(j=0;j<11;++j)masks[i][j]='?';
 assert(refresh());
 /* Set a scrolled file-view checkpoint. */
 browser.navigation.selected=100;browser.navigation.offset=40;
 assert(fm_marks_key(&marks,2,120,44)==1);
 assert(drive_view() && drives);
 assert(directory_view() && directories && browser.navigation.count==1);
 assert(drive_view() && drives);
 assert(picker_cancel());
 assert(browser.navigation.selected==100 && browser.navigation.offset==40);
 assert(marks.count==1 && marks.value[1]);
 assert(fm_browser_key(&browser,0xc2)>=0);
 assert(directory_view());assert(picker_cancel());
 assert(marks.count==1);
 saved_selection=0;assert(picker_cancel());assert(browser.navigation.selected==1);
 saved_selection=999;assert(picker_cancel());assert(browser.navigation.selected==1);
 /* Copy's CP/M user picker must retain source user and marked files. */
 fat=0;user=4;assert(refresh());
 browser.navigation.selected=20;browser.navigation.offset=10;
 copy_user_choosing=1;assert(directory_view());
 browser.navigation.selected=5;assert(copy_user_select());
 assert(copy_user_choosing && user==4 && marks.count==1);
 browser.navigation.selected=6;assert(copy_user_select());
 assert(!copy_user_choosing && !directories && user==4);
 assert(browser.navigation.selected==20 && marks.count==1);
 assert(drive_view());assert(drive_select());assert(marks.count==0);
 assert(fm_marks_key(&marks,1,120,44)==1);
 fm_input_open(&input);assert(subset_key(13));assert(marks.count==0);
 /* Bookmarks: setting current FAT directory preserves original file marks. */
 drive=1;fat=1;user=0;assert(refresh());
 fm_marks_key(&marks,3,120,44);assert(directory_view());
 assert(names[0]==current_directory);assert(book_set(0));
 assert(bookmarks[0].set && bookmarks[0].drive==14 && pins[14]==1);
 assert(!strcmp(notice,"DIR #1 set to: A:."));assert(marks.count==1);
 /* Failed replacement must retain pinned original and report failure. */
 capture_result=0;location_error=1;assert(book_set(0));
 assert(bookmarks[0].drive==14 && pins[14]==1 && strcmp(notice,"DIR #1 set to: A:."));
 capture_result=15;location_error=0;assert(book_set(0));
 assert(bookmarks[0].drive==15 && pins[14]==0 && pins[15]==1);
 /* Copy destination pickers cannot redefine saved destinations. */
 copy_user_choosing=1;assert(book_set(1));assert(!bookmarks[1].set);
 copy_user_choosing=0;assert(picker_cancel());
 assert(book_set(1));assert(!bookmarks[1].set);
 assert(book_go(1) && !strcmp(notice,"first set Dir #2"));
 /* Navigation selects a clone outside physical-drive mask, keeps pinned alias. */
 assert(book_go(0));assert(drive==16 && clones==1 && pins[15]==1 && !marks.count);
 assert(drive_view());assert(drive_count==3 && drive_numbers[2]==16);
 browser.navigation.selected=3;assert(drive_select() && drive==16);
 /* Saved FAT copy uses pinned directory identity, rejects same location. */
 drive=1;fat=1;assert(refresh());copy_menu=1;same_location=1;
 assert(copy_key(0xc1) && !copy_calls && copy_menu);
 same_location=0;location_error=1;assert(copy_key(0xc1) && !copy_calls && copy_menu);
 location_error=0;assert(copy_key(0xc1) && copy_calls==1 && lastdest==15 && !copy_menu);
 /* Immutable CP/M drive/user snapshots, independent target users and drives. */
 fat=0;drive=2;user=4;assert(directory_view());browser.navigation.selected=7;
 assert(book_set(1));assert(bookmarks[1].drive==2 && bookmarks[1].user==6);
 assert(!strcmp(notice,"DIR #2 set to: B:User 06"));
 assert(picker_cancel());drive=1;user=3;copy_menu=1;
 assert(copy_key(0xc2) && batch_calls==2 && lastdest==2 && lastuser==6 && user==3);
 assert(book_go(1));assert(drive==2 && user==6 && !fat);
 /* UI selection changes do not alter a saved CP/M bookmark. */
 assert(directory_view());browser.navigation.selected=2;assert(picker_cancel());
 assert(book_go(1) && user==6);
 /* Invalidate FAT bookmark: neither navigate nor copy. */
 valid_alias=0;i=clones;j=copy_calls;assert(book_go(0) && clones==i);
 assert(copy_book(0) && copy_calls==j);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 modules='book config menu focus select marks screen layout frame keys navigate dirlist browse conio'.split()
 subprocess.run(['cc','-DHOST_TEST','-std=c89','-Wno-deprecated-non-prototype','-Wno-incompatible-library-redeclaration','-I',str(root),str(src)]+[str(root/(m+'.c')) for m in modules]+['-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: nested pickers, empty picker, saved selection, marks retained on cancel and cleared on acceptance')
