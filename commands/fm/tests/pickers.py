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
int __BDOS(){return 0;}
int fm_view_files(){return 1;}
int fm_print_files(){return 1;}
int fm_rename_file(){return 1;}
int fm_rename_files(){return 1;}
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
 assert(directory_view() && directories && browser.navigation.count==0);
 assert(drive_view() && drives);
 assert(picker_cancel());
 assert(browser.navigation.selected==100 && browser.navigation.offset==40);
 assert(marks.count==1 && marks.value[1]);
 assert(fm_browser_key(&browser,0xc2)>=0);
 assert(directory_view());assert(picker_cancel());
 assert(marks.count==1);
 saved_selection=0;assert(picker_cancel());assert(browser.navigation.selected==1);
 saved_selection=999;assert(picker_cancel());assert(browser.navigation.selected==1);
 assert(drive_view());assert(drive_select());assert(marks.count==0);
 assert(fm_marks_key(&marks,1,120,44)==1);
 fm_input_open(&input);assert(subset_key(13));assert(marks.count==0);
 return 0;
}
"""
with tempfile.TemporaryDirectory() as tmp:
 src=Path(tmp)/'check.c';src.write_text(source);exe=Path(tmp)/'check'
 modules='config menu focus select marks screen layout frame keys navigate dirlist browse conio'.split()
 subprocess.run(['cc','-DHOST_TEST','-std=c89','-Wno-deprecated-non-prototype','-Wno-incompatible-library-redeclaration','-I',str(root),str(src)]+[str(root/(m+'.c')) for m in modules]+['-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: nested pickers, empty picker, saved selection, marks retained on cancel and cleared on acceptance')
