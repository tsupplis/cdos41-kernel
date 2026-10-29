/*  MEDSCR.C    -   Screen definitions for the Menu Edit utility */

/*                  Copyright (c) 1984      RTEK Inc.                       */
/*                                          2265 E. Becker Lane             */
/*                                          Phoenix, Arizona 85028          */
/*                                          (602) 867-9336                  */
/*  last mod:  5 MAR 85...JMB...serial terminal support			    */
/*  new source lines -> "/*;"						    */

#include <portab.h>
#include "scrsubs.h"
#include <attr.h>
#include "edupmsgs.h"		/*; keyboard-specific msgs. */

/*** Screen Title **********************************************************/

struct  scr_msg     title =
    { 24, 0, 1, TIT_A, "MENU CREATION AND MODIFICATION" };


/*** MED screen 00 **********************************************************/

struct  scr_msg     med_00a[] =
{
    { 09, 05, 1, BKG_A, "Please Select:" }
   ,{ 18, 07, 1, OPT_A, sq_msg_1 }
   ,{ 18, 08, 1, OPT_A, sq_msg_2 }
   ,{ 18, 09, 1, OPT_A, sq_msg_3 }
   ,{ 18, 10, 1, OPT_A, sq_msg_4 }
   ,{ 18, 11, 1, OPT_A, " Esc Exit Editmenu       " }
};
        WORD    medc_00a = MSG_CNT(med_00a);  /* number of elements in screen */

/*** MED screen 01 **********************************************************/

struct  scr_msg     med_01a[] =
{
    {  3,  3, 1, BKG_A, "Enter New Menu Name:" }
   ,{  3,  5, 1, OPT_A, sq_msg_5 }
   ,{  3,  6, 1, OPT_A, "   Press Esc to Return to Previous Screen" }
};
        WORD    medc_01a = MSG_CNT(med_01a);  /* number of elements in screen*/

struct  scr_msg     med_01b[] =
{
    {  3,  3, 1, BKG_A, "Enter New Menu Name:" }
   ,{  3,  5, 1, BKG_A, "Enter Name of Existing Menu to copy:" }
   ,{  3,  7, 1, OPT_A, sq_msg_5 }
   ,{  3,  8, 1, OPT_A, "   Press Esc to Return to Previous Screen" }
};
        WORD    medc_01b = MSG_CNT(med_01b);  /* number of elements in screen */

struct  scr_msg     med_01c[] =
{
    {  3,  3, 1, BKG_A, "Enter Menu Name to Change:" }
   ,{  3,  5, 1, OPT_A, sq_msg_5 }
   ,{  3,  6, 1, OPT_A, "   Press Esc to Return to Previous Screen" }
};
        WORD    medc_01c = MSG_CNT(med_01c);  /* number of elements in screen*/

struct  scr_msg     med_01d[] =
{
    {  3,  3, 1, BKG_A, "Enter Menu Name to Delete:" }
   ,{  3,  5, 1, OPT_A, sq_msg_5 }
   ,{  3,  6, 1, OPT_A, "   Press Esc to Return to Previous Screen" }
};
        WORD    medc_01d = MSG_CNT(med_01d);  /* number of elements in screen*/

struct  scr_msg     med_01e[] =
{
    {  3,  8, 1, BKG_A, "Delete This Menu? (Y/N)" }
};
        WORD    medc_01e = MSG_CNT(med_01e);  /* number of elements in screen */

struct  scr_msg     med_01f[] =
{
    {  3, 10, 1, ERR_A, "Cannot find menu to copy.  Press [ANY KEY]" }
};
        WORD    medc_01f = MSG_CNT(med_01f);  /* number of elements in screen */

struct  scr_msg     med_01g[] =
{
    {  3, 10, 1, ERR_A, "No room in directory for new menu.  Press [ANY KEY]" }
};
        WORD    medc_01g = MSG_CNT(med_01g);  /* number of elements in screen */

struct  scr_msg     med_01h[] =
{
    {  3, 10, 1, ERR_A, "Menu corrupted, menu deleted.  Press [ANY KEY]" }
};
        WORD    medc_01h = MSG_CNT(med_01h);  /* number of elements in screen */

struct  scr_msg     med_01i[] =
{
    {  3, 10, 1, ERR_A, "Menu not found.  Press [ANY KEY]" }
};
        WORD    medc_01i = MSG_CNT(med_01i);  /* number of elements in screen */

struct  scr_msg     med_01j[] =
{
    {  3, 10, 1, ERR_A, "Menu Exists.  Press [ANY KEY]" }
};
        WORD    medc_01j = MSG_CNT(med_01j);  /* number of elements in screen */

/*** MED screen 02 **********************************************************/

struct  scr_msg     med_02a[] =
{
    { 04, 23, 1, OPT_A, "Press [ANY KEY] to Continue..." }
};
        WORD    medc_02a = MSG_CNT(med_02a);  /* number of elements in screen */

/*** MED screen 03 **********************************************************/

/*** MED screen 04 **********************************************************/

struct  scr_msg     med_04a[] =
{
    { 00, 21, 1, OPT_A, sq_msg_36}
   ,{ 00, 22, 1, OPT_A, sq_msg_6 }
   ,{ 00, 23, 1, OPT_A, sq_msg_7 }
};
        WORD    medc_04a = MSG_CNT(med_04a);  /* number of elements in screen */

struct  scr_msg     med_04b[] =
{
    { 00, 21, 1, ERR_A, " Exit Without Changes? (Y/N)  " }
   ,{ 29, 21, 1, ERR_A, "N" }
   ,{ 30, 21, 1, DEF_A, "                             " }
};
        WORD    medc_04b = MSG_CNT(med_04b);  /* number of elements in screen */

struct  scr_msg     med_04c[] =
{
    { 00, 21, 1, BKG_A, " Please Enter: Source Start Row     End Row     Destin\
ation Start Row   " }
   ,{ 32, 21, 1, MOD_A, "00" /* Source start row */ }
   ,{ 44, 21, 1, MOD_A, "00" /* Source end row */ }
   ,{ 70, 21, 1, MOD_A, "00" /* Destination start row */ }
   ,{ 00, 22, 1, OPT_A, sq_msg_8 }
   ,{ 00, 23, 1, OPT_A, "    or Press Esc to cancel the copy  " }
};
        WORD    medc_04c = MSG_CNT(med_04c);  /* number of elements in screen */

struct  scr_msg     med_04d[] =
{
    { 00, 21, 1, OPT_A,sq_msg_9 }
};
        WORD    medc_04d = MSG_CNT(med_04d);  /* number of elements in screen */

struct  scr_msg     med_04e[] =
{
    { 50, 21, 1, BKG_A, "Column: " }
   ,{ 58, 21, 1, BKG_A, "00" /* column number */ }
   ,{ 62, 21, 1, BKG_A, "  Line: " }
   ,{ 70, 21, 1, BKG_A, "00" /* line number */  }
};
        WORD    medc_04e = MSG_CNT(med_04e);  /* number of elements in screen */

struct  scr_msg     med_04f[] =
{
    { 00, 22, 1, BKG_A, " Reverse Video" }
   ,{ 17, 22, 1, BKG_A, "Underscore" }
   ,{ 31, 22, 1, BKG_A, "Bright" }
   ,{ 41, 22, 1, BKG_A, "Blink" }
   ,{ 50, 22, 1, BKG_A, "Foreground" }
   ,{ 64, 22, 1, BKG_A, "Background" }
};
        WORD    medc_04f = MSG_CNT(med_04f);  /* number of elements in screen */

struct  scr_msg     med_04g[] =
{
    { 00, 23, 1, BKG_A, "  Black  " }
   ,{ 09, 23, 1, BKG_A, "  Blue   " }
   ,{ 18, 23, 1, BKG_A, "  Green  " }
   ,{ 27, 23, 1, BKG_A, "   Red   " }
   ,{ 36, 23, 1, BKG_A, "  Cyan   " }
   ,{ 45, 23, 1, BKG_A, " Magenta " }
   ,{ 54, 23, 1, BKG_A, " Yellow  " }
   ,{ 63, 23, 1, BKG_A, "  White  " }
};
        WORD    medc_04g = MSG_CNT(med_04g);  /* number of elements in screen */

struct  scr_msg     med_04i[] =
{
    { 00, 21, 1, OPT_A, sq_msg_10 }
};
        WORD    medc_04i = MSG_CNT(med_04i);  /* number of elements in screen */

/*** MED screen 05 **********************************************************/

struct  scr_msg     med_05a[] =
{
    { 71, 23, 1, SP1_A, "[ANY KEY]" }       /* reverse video */
};
        WORD    medc_05a = MSG_CNT(med_05a);  /* number of elements in screen */

/*** MED screen 06 **********************************************************/

struct  scr_msg     med_06a[] =
{
    { 03, 02, 1, BKG_A, "Use the following Functions While You Edit a Menu on t\
he Previous Screen" }
   ,{ 07, 03, 1, BKG_A, sq_msg_37 }
   ,{ 07, 04, 1, BKG_A, sq_msg_11 }
   ,{ 07, 05, 1, BKG_A, sq_msg_12 }
   ,{ 07, 06, 1, BKG_A, sq_msg_13 }
   ,{ 07, 07, 1, BKG_A, sq_msg_14 }
   ,{ 07, 08, 1, BKG_A, sq_msg_15 }
   ,{ 07, 09, 1, BKG_A, sq_msg_16 }
   ,{ 07, 10, 1, BKG_A, sq_msg_17 }
   ,{ 07, 11, 1, BKG_A, sq_msg_18 }
   ,{ 07, 12, 1, BKG_A, sq_msg_19 }
   ,{ 07, 13, 1, BKG_A, sq_msg_20 }
   ,{ 03, 15, 1, BKG_A,
  "Use the Following Control Keys While You Edit a Menu:" }
   ,{ 00, 17, 1, BKG_A, sq_msg_21 }
   ,{ 00, 18, 1, BKG_A, sq_msg_22 }
   ,{ 00, 19, 1, BKG_A, sq_msg_23 }
   ,{ 00, 20, 1, BKG_A, sq_msg_24 }
   ,{ 00, 21, 1, BKG_A, sq_msg_38 }
   ,{ 00, 22, 1, BKG_A, sq_msg_25 }
   ,{ 40, 17, 1, BKG_A, sq_msg_26 }
   ,{ 40, 18, 1, BKG_A, sq_msg_27 }
   ,{ 40, 19, 1, BKG_A, "TAB       Cursor to next tab stop" }
   ,{ 40, 20, 1, BKG_A, sq_msg_28 }
   ,{ 40, 21, 1, BKG_A, "ENTER     Cursor to next line" }
   ,{ 40, 22, 1, BKG_A, "BACKSPACE Erase prior character" }
   ,{ 05, 23, 1, OPT_A, sq_msg_29 }
};
        WORD    medc_06a = MSG_CNT(med_06a);  /* number of elements in screen */

/*** MED screen 07 **********************************************************/

struct  scr_msg     med_07a[] =
{
    { 03, 02, 1, BKG_A, "You can use the following symbols to create special ef\
fects on the menu" }
   ,{ 03, 03, 1, BKG_A, "screen.  You must define the menu screen from left to \
right and from top " }
   ,{ 03, 04, 1, BKG_A, "to bottom.  Special effects remain defined until you c\
hange them. " }
   ,{ 03, 05, 1, BKG_A, "At the start of the menu, the following settings are\
 in effect: bright off;" }
   ,{ 03, 06, 1, BKG_A, "underline off; blink off; black background; and white \
foreground.  The" }
   ,{ 03, 07, 1, BKG_A, "Special Effect symbols are:" }
   ,{ 06, 09, 1, BKG_A, "\\  to start or end reverse video." }
   ,{ 06, 10, 1, BKG_A, "_  to start or end underline (Monochrome Display only)\
."    }
   ,{ 06, 11, 1, BKG_A, "}  to start or end bright display." }
   ,{ 06, 12, 1, BKG_A, "{  to start or end blinking display." }
   ,{ 06, 13, 1, BKG_A, "|c to set background color to 'c' starting at | positi\
on." }
   ,{ 06, 14, 1, BKG_A, "|C to set background color to 'c' starting after 'c' p\
osition." }
   ,{ 06, 15, 1, BKG_A, "~c to set foreground color to 'c' (see color list belo\
w)." }
   ,{ 06, 17, 1, BKG_A, "The colors are:" }
   ,{ 27, 17, 1, BKG_A, "k = Black        c = Cyan" }
   ,{ 27, 18, 1, BKG_A, "b = Blue         m = Magenta" }
   ,{ 27, 19, 1, BKG_A, "g = Green        y = Yellow" }
   ,{ 27, 20, 1, BKG_A, "r = Red          w = White" }
   ,{ 03, 22, 1, OPT_A, "Press [ANY KEY] to Return to Previous Screen" }
};
        WORD    medc_07a = MSG_CNT(med_07a);  /* number of elements in screen */

/*** MED screen 08 **********************************************************/

struct  scr_msg     med_08a[] =
{
    { 03, 02, 1, BKG_A, "Disable ESC to return to prior menu level? (Y/N)" }
   ,{ 03, 03, 1, BKG_A, "     Note:  The prior menu level is the system  " }
   ,{ 03, 04, 1, BKG_A, "            prompt if this is the main menu.    " }
   ,{ 03, 05, 1, BKG_A, "Disable ENTER to enter a command in Concurrent DOS For\
mat? (Y/N)" }
   ,{ 03, 06, 1, BKG_A, "Save and restore default drive? (Y/N)           " }
   ,{ 03, 07, 1, BKG_A, "Save and restore User number ? (Y/N)            " }
/* ,{ 03, 08, 1, BKG_A, "Save and restore path? (Y/N)                    " }*/
/* ,{ 03, 09, 1, BKG_A, "Save and restore map? (Y/N)                     " }*/
   ,{ 03, 11, 1, BKG_A, "Command to execute at start of menu:            " }
   ,{ 03, 15, 1, BKG_A, "Command to execute at end of menu:              " }
   ,{ 03, 20, 1, OPT_A, sq_msg_30 }
};
        WORD    medc_08a = MSG_CNT(med_08a);  /* number of elements in screen */

/*** MED screen 09 **********************************************************/

struct  scr_msg     med_09a[] =
{
    { 03, 02, 1, BKG_A, "You must enter Function Key Assignments for all Funct\
ion Keys used on the" }
   ,{ 03, 03, 1, BKG_A, "current menu.  There are two parts to a Function Key A\
ssignment: the" }
   ,{ 03, 04, 1, BKG_A, "Command Type, and Command Text or Menu Name.  You can \
enter more than one" }
   ,{ 03, 05, 1, BKG_A, "command on a line if you seperate them with an '!'." }
   ,{ 03, 07, 1, BKG_A, "The Command Types are:" }
   ,{ 02, 09, 1, BKG_A, "    A - Application command line in its complete form."
 }
   ,{ 02, 10, 1, BKG_A, "    O - Command line with Options to be entered by\
 the user at run time." }
   ,{ 02, 11, 1, BKG_A, "        For example, DIR may require options to be \
entered." }
   ,{ 02, 12, 1, BKG_A, "    M - Menu.  Enter the menu name of the sub-menu\
 to be displayed." }
   ,{ 02, 13, 1, BKG_A, "    C - Command to be entered entirely by the user\
 at run time." }
   ,{ 02, 14, 1, BKG_A, "    E - Exit the menu program to the operating system."
  }
   ,{ 02, 15, 1, BKG_A, "Blank - Function Key not used in this menu." }
   ,{ 02, 17, 1, BKG_A, "The following keys are automatically implemented on me\
nus as a default:" }
   ,{ 02, 18, 1, BKG_A, "  ESC - Return to Previous Screen" }
   ,{ 02, 19, 1, BKG_A, "ENTER - Allows you to enter a command at the operating\
 system prompt." }
   ,{ 02, 20, 1, BKG_A, sq_msg_31 }
   ,{ 02, 21, 1, BKG_A, "of ESC and ENTER." }
   ,{ 03, 23, 1, BKG_A, "Press [ANY KEY] to Return to Previous Screen" }
};
        WORD    medc_09a = MSG_CNT(med_09a);  /* number of elements in screen */

/*** MED screen 10 **********************************************************/

struct  scr_msg     med_10a[] =
{
    { 00, 01, 1, TIT_A, "Fcn    Type   Menu Name or Command Text" }
   ,{ 01, 02, 1, BKG_A, " 1" }
   ,{ 01, 04, 1, BKG_A, " 2" }
   ,{ 01, 06, 1, BKG_A, " 3" }
   ,{ 01, 08, 1, BKG_A, " 4" }
   ,{ 01, 10, 1, BKG_A, " 5" }
   ,{ 01, 12, 1, BKG_A, " 6" }
   ,{ 01, 14, 1, BKG_A, " 7" }
   ,{ 01, 16, 1, BKG_A, " 8" }
   ,{ 01, 18, 1, BKG_A, " 9" }
   ,{ 01, 20, 1, BKG_A, sq_msg_32 }
   ,{ 00, 22, 1, OPT_A, sq_msg_33 }
   ,{ 00, 23, 1, OPT_A, sq_msg_34 }
};
        WORD    medc_10a = MSG_CNT(med_10a);  /* number of elements in screen */

/*** MED screen 11 **********************************************************/

struct  scr_msg     med_11a[] =
{
    { 03, 02, 1, BKG_A, "Do you want to save this menu? (Y/N)" }
   ,{ 03, 04, 1, OPT_A, "Press ESC to Return to Previous Screen" }
};
        WORD    medc_11a = MSG_CNT(med_11a);  /* number of elements in screen */

/*** MED screen 12 *********************************************************/

struct  scr_msg     med_12a[] =
{
    {  3,  4, 1, BKG_A, "Enter Existing Menu File Name:" }
   ,{  3,  6, 1, OPT_A, sq_msg_35 }
   ,{ 32,  6, 1, OPT_A, " " }       /* menu name goes here */
   ,{  3,  7, 1, OPT_A, "   Press Esc to exit Editmenu          " }
};
    WORD    medc_12a = MSG_CNT(med_12a);  /* number of elements in screen */

struct  scr_msg     med_12b[] =
{
    {  3,  9, 1, ERR_A, "The Menu file: " },
    { 18,  9, 1, ERR_A, ""/* file name */ },
    { 33,  9, 1, ERR_A, "is corrupted.  Press [ANY KEY]" }
};
    WORD    medc_12b = MSG_CNT(med_12b);  /* number of elements in screen */

struct  scr_msg     med_12c[] =
{
    {  3, 12, 1, BKG_A, "Enter Menu File Name to Create:" },
    {  3, 14, 1, OPT_A, "or Press Esc to Return to Previous Screen" }
};
    WORD    medc_12c = MSG_CNT(med_12c);  /* number of elements in screen */

struct  scr_msg     med_12d[] =
{
    {  3,  2, 1, ERR_A, "File: " },
    {  9,  2, 1, ERR_A, ""/* file name */ },
    { 26,  2, 1, ERR_A, "not found or Read-Only" }
};
        WORD    medc_12d = MSG_CNT(med_12d);  /* number of elements in screen */

struct  scr_msg     med_12e[] =
{
    {  3,  4, 1, ERR_A, "Requires Concurrent DOS Version 3.2 or Greater" }
   ,{  3,  6, 1, ERR_A, "Press [ANY KEY]" }
};
        WORD    medc_12e = MSG_CNT(med_12e);  /* number of elements in screen */

struct  scr_msg     med_12f[] =
{
    {  3,  4, 1, ERR_A, "Unexpected System Error, Can't Continue." }
   ,{  3,  6, 1, ERR_A, "Press [ANY KEY]" }
};
        WORD    medc_12f = MSG_CNT(med_12f);  /* number of elements in screen */

struct  scr_msg     med_12g[] =
{
    {  3,  4, 1, ERR_A, "Can't Create New File.  Press [ANY KEY]" }
};
        WORD    medc_12g = MSG_CNT(med_12g);  /* number of elements in screen */

struct  scr_msg     med_12h[] =
{
    {  3,  4, 1, ERR_A, "Initialization Failed, no memory.  EDITMENU Abort.  Pr\
ess [ANY KEY]" }
};
        WORD    medc_12h = MSG_CNT(med_12h);  /* number of elements in screen */

struct  scr_msg     med_12i[] =
{
    {  3,  4, 1, ERR_A, "Error Writing Menu, EDITMENU Abort.  Press [ANY KEY]" }
};
        WORD    medc_12i = MSG_CNT(med_12i);  /* number of elements in screen */


    /* the model, do not modify */

/*** MED screen nn **********************************************************/
/*  <----------------------- TAKE THIS OUT !!!
struct  scr_msg     med_nna[] =
{
    {  C,  L, 1, DEF_A, "" }
   ,{  C,  L, 1, DEF_A, "" }
   ,{  C,  L, 1, DEF_A, "" }
   ,{  C,  L, 1, DEF_A, "" }
   ,{  C,  L, 1, DEF_A, "" }
   ,{  C,  L, 1, DEF_A, "" }
};
        WORD    medc_NNa = MSG_CNT(med_NNa);  /* number of elements in screen */

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  