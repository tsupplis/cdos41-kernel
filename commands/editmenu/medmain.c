/*	MEDMAIN.C  - Edit the MENUs					    */

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */

/*	Last mod: 4 MAR 85...JMB					    */
/*	Add support for serial terminals				    */
/*	New source lines marked by /*;*/	
/*** INCLUDE FILES **********************************************************/

#include <stdio.h>
#include "menu.h"
#include "fkeys.h"
#include "iosubs.h"
#include "attr.h"
#include "scrsubs.h"

/*** DEFINES ***************************************************************/

#define	MAIN			/*;*/

#define USER_EXIT   2		/* return code for user requested exit */
#define GO_BACK     3		/* go back to prior step return code */
#define NO_MEMORY   4		/* No memory available return from init */
#define NO_TERM_DATA 5		/*; No TERM.DAT file located */
#define READWRITE   2		/* open mode for read/write */

/*  defines for calling WM_PK (peek & poke to vc_)  */

#define PEEK	    0
#define POKE	    1
#define CUR_TYPE    62			/* cursor type index (low byte) */
#define MONO_TYPE   0x09		/* monochrome monitor value */
#define CRT_SEG     24			/*; VIDEO BUFF segment */
#define MONO_SEG   0xB000
#define COLOR_SEG  0xB800

/* Defines for Edit_Menu() */

#define EDIT_SCREEN	1
#define EDIT_FUNCTION	2
#define EDIT_SAVE	3
#define EDIT_WRITE	4
#define EDIT_DONE	5

/*  Defines for med screen 12 function */

#define M12_OPENOLD	1
#define M12_READDIR	2
#define M12_BADDIR	3
#define M12_NOFILE	4
#define M12_MAKENEW	5
#define M12_CANTMAKE	6
#define M12_STARTOVER	7
#define M12_EXITPROG	8
#define M12_SCR_DUN	9
#define M12_GET_F_NAME 10

#define	C_GET	153

/*** STRUCTURE DECLARATIONS ************************************************/

/*** EXTERNAL FUNCTION DECLARATIONS ****************************************/

EXTERN	BYTE	*malloc();
EXTERN	WORD	creatb();

EXTERN	WORD	any_key();	    /* in iosubs.c	*/

EXTERN	VOID	clr_mnu();	    /* in MENUSUB.C	*/
EXTERN	WORD	rd_dir();
EXTERN	WORD	wr_dir();
EXTERN	WORD	wr_mnu();
EXTERN	WORD	upd_dir();
EXTERN	WORD	fnd_mnu();
EXTERN	VOID	del_mnu();
EXTERN	WORD	rd_mnu();
EXTERN	WORD	compres();
EXTERN	WORD	expand();

EXTERN	VOID	p_msg();	    /* in scrsubs.c */
EXTERN	VOID	p_msgs();
EXTERN	VOID	scr_beg();
EXTERN	VOID	scr_end();
EXTERN	VOID	clr_scr();

EXTERN	BOOLEAN med_00();	    /* in medscr1.c */
EXTERN	WORD	med_04();	    /* in medscr2.c */
EXTERN	WORD	med_10();	    /* in medscr3.c */
EXTERN	WORD	med_11();	    /* in medscr4.c */
EXTERN	WORD	med_12();

EXTERN	VOID	WM_PK();	    /* in WWCALL.A86 */

/*** EXTERNAL VARIABLES ****************************************************/

/*** GLOBAL VARIABLES ******************************************************/

GLOBAL	BYTE	*menu_dir;		    /* the directory */
GLOBAL	WORD	menu_rec[DIRCOUNT];	    /* pointers to start of menus  */
GLOBAL	BYTE	*scr_work;		    /* working screen */

GLOBAL	BYTE	m1_name[16] = { "MENU.DAT" };  /* current menu file name    */
GLOBAL	BYTE	m2_name[16] = { "MENU.DAT" }; /* alternate menu file name   */
GLOBAL	WORD	m1_fd;			    /* menu file fd		    */
GLOBAL	WORD	m2_fd;			    /* alternate menu file fd	    */

GLOBAL	struct	f_keys	*key_ptr = &squid_keys;	/*; for serial vs. sq. keys */

GLOBAL	struct f_keys squid_keys = {		/*;*/
		0xBB, 0xBC, 0xBD, 0xBE, 0xBF,	/*;*/
		0xC0, 0xC1, 0xC2, 0xC3, 0xC4,	/*;*/
		0xC7, 0xCF			/*; HOME, END */
	};					/*;*/

GLOBAL	struct f_keys ser_keys = {		/*;*/
		01, 02,				/*; cntl a, cntl b */
		16, 17, 18, 19, 20, 21, 22, 23,	/*; cntl p - cntl w*/
		03,				/*; HOME = cntl c */
		14				/*; END = cntl n */			
	};					/*;*/


/*** Other Static Variables *************************************************/

MLOCAL	struct	menu	*mp;		    /* the main menu structure	    */
MLOCAL	struct	menu	the_menu;	    /* allocate storeage	    */

/*** MAIN FUNCTION *********************************************************/

main(argc, argv)

	WORD	argc;
	BYTE	*argv[];
{
	WORD	ret;			/* return code */
	BOOLEAN edit_more;		/* done with edit */

EXTERN	BYTE	*cur_attr;	/* current attribute table */

/*  Screen Messages */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_12h[];
EXTERN	WORD	medc_12h;

/*    if (__BDOS(C_GET,0x0) > 3){				/*;*/
/*	printf("\nEDITMENU cannot run on this terminal.\n");	/*;*/
/*	exit(-1);						/*;*/
/*    }								/*;*/

    ret = init(argc, argv);	    /* initialize for edit */
    if (ret == NO_MEMORY)	    /* if initialization fails, */
    {
	scr_beg();		    /* clear the screen */
	clr_scr(cur_attr[DEF_A]);   /* with default attribute */
	p_msg(&title);		    /* print the title */
	p_msgs(med_12h, medc_12h); /* no memory abort message */
	scr_end();
	any_key();		    /* any character */
	clean_up();		    /* abort */
    }
    if (ret == USER_EXIT)
	clean_up();		    /* user exit requested */

    if (ret == NO_TERM_DATA) {					/*;*/
	printf("\nEDITMENU cannot run on this terminal.\n");	/*;*/
/*;	clean_up();		because don't know scrn codes	   */
	exit(-1);						/*;*/
    }								/*;*/

    edit_more = TRUE;		     /* done flag */
    while (edit_more)
    {
	ret = med_00(mp);
	if (ret == USER_EXIT)
	    edit_more = FALSE;
    }
    clean_up();
}

/*** SUB FUNCTIONS *********************************************************/

/*** EDIT a MENU **************************************************************/

BOOLEAN edit_menu( mp )

struct	menu	*mp;		    /* the menu structure */
{
	WORD	ret;		    /* temp for return */
	WORD	cur_step;	    /* current step in menu definition */

EXTERN	BYTE	*cur_attr;	/* current attribute table */

/*  Screen Messages */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_12i[];
EXTERN	WORD	medc_12i;

    cur_step = EDIT_SCREEN;	    /* start with edit screen */
    while (cur_step != EDIT_DONE)   /* until menu definition complete */
    {
	switch(cur_step)
	{
	case EDIT_SCREEN:
	    ret = med_04(mp);		    /* edit the menu screen */
	    if (ret != SUCCESS)
		return(ret);		    /* return status */
	    cur_step = EDIT_FUNCTION;	    /* on to define functions */
	    break;

	case EDIT_FUNCTION:
	    ret = med_10(mp);		    /* define the functions */
	    if (ret == FAILURE)
		return(ret);		    /* fail means abort menu */
	    if (ret == GO_BACK)
	    {
		cur_step = EDIT_SCREEN;     /* go back to edit screen */
		break;
	    }
	    cur_step = EDIT_SAVE;
	    break;

	case EDIT_SAVE:
	    ret = med_11();		    /* see if user wants to save menu */
	    if (ret == FAILURE)
		return(TRUE);		    /* nope, don't write */
	    if (ret == SUCCESS)
	    {
		cur_step = EDIT_WRITE;
		break;
	    }
	    cur_step = EDIT_FUNCTION;
	    break;

	case EDIT_WRITE:
	    ret = wr_mnu( m1_fd, mp );	    /* write the menu to file */
	    if (ret == 0)
	    {
		scr_beg();		    /* clear the screen */
		clr_scr(cur_attr[DEF_A]);   /* with default attribute */
		p_msg(&title);		    /* print the title */
		p_msgs(med_12i, medc_12i); /* error writing menu abort message *
		scr_end();
		any_key();		    /* any character */
		return (FALSE); 	    /* abort */
	    }
	    cur_step = EDIT_DONE;
	    break;

	}   /* switch */
    }	/* while */
/*	All ok, update and write the directory	*/

    menu_rec[mp->menu_num] = ret;		    /* store menu rec no */
    upd_dir( menu_dir, mp->menu_num, mp->menu_name );
    wr_dir( m1_fd, menu_dir, &menu_rec[0] );
    close(m1_fd);			    /* close the menu file */
    m1_fd = openb(m1_name, READWRITE);	    /* re-open the menu file */
    return(TRUE);
}

/*** INITialize for editing a menu *****************************************/

GLOBAL	BOOLEAN is_mono;		/* TRUE if monochrome monitor */

WORD	init(argc, argv)
	WORD	argc;
	BYTE	*argv[];
{
	WORD	ret;		/* return value */
	WORD	i,j;		/* temp counter */
	BYTE	*ptr;		/* temp pointer */
	UWORD	screen_base;	/*; where the PC phys. screen buff. is. */

EXTERN	BOOLEAN v31;		/* version number we are running under */
EXTERN	WORD	vc_number;	/* our virtual console number */
EXTERN	BYTE	*cur_attr;	/* current attribute table */
EXTERN	BYTE	col_attr[];	/* color attribute table */
EXTERN	struct	scr_msg med_12e;
EXTERN	WORD	medc_12e;
EXTERN	UWORD	ser_term_init(); 		/*; check for TERM.DAT */
EXTERN	BYTE	sq_msg_1[], sq_msg_last[];	/*; term-spec. msgs */
EXTERN	BYTE	ser_msg_1[], ser_msg_last[];	/*; term-spec. msgs */

    mp = &the_menu;		/* store address of menu */
    wm_init();			/* initialize for direct virtual i/o */

/**********  set up the proper cur_attr depending on screen type **********/
/*;********  but first, make sure it's a PC-windowed screen ***************/

    WM_PK(PEEK, vc_number, CRT_SEG, &screen_base);			/*;*/

    if ((screen_base != COLOR_SEG) && (screen_base != MONO_SEG)) {	/*;*/
	if(ser_term_init(vc_number) == 0xffff) return(NO_TERM_DATA);	/*;*/
	else {								/*;*/
	 is_mono = TRUE;						/*;*/
	 key_ptr = &ser_keys;						/*;*/
	 (BYTE*)i =  &sq_msg_last[0] -  &sq_msg_1[0];			/*;*/
	 (BYTE*)j = &ser_msg_last[0] - &ser_msg_1[0];			/*;*/
	 if (i != j) return(NO_TERM_DATA);				/*;*/
	 for (i=0; i<j; i++) sq_msg_1[i]=ser_msg_1[i];	/*; overlay	   */
	 wrap_on();							/*;*/
	}								/*;*/
    }									/*;*/

    else {								/*;*/
     key_ptr = &squid_keys;						/*;*/
     wrap_off();
     WM_PK(PEEK, vc_number, CUR_TYPE, &i);   /* get cursor type */
     if ( (i & 0x00ff) != MONO_TYPE)	    /* if not mono, set attr to color */
     {
	cur_attr = &col_attr[0];
	is_mono = FALSE;
     }
     else
	is_mono = TRUE;
    }									/*;*/

    scr_beg();			/* clear the screen */
    clr_scr(cur_attr[DEF_A]);	/* with default attribute */
    scr_end();

    if (v31 == FALSE)
    {
	scr_beg();		    /* clear the screen */
	clr_scr(cur_attr[DEF_A]);   /* with default attribute */
	p_msg(&title);		    /* print the title */
	p_msgs(&med_12e, medc_12e); /* not correct version message */
	scr_end();
	any_key();		    /* any character */
	return(USER_EXIT);	    /* init failed */
    }

    menu_dir = malloc(DIRSIZE + 1);  /* allocate directory space */
    if (menu_dir == NULL)
	return(NO_MEMORY);	/* return if can't get memory */

    for (i = 0; i < 16; i++)	/* allocate space for commands */
    {
	ptr = malloc(129);	/* 1 command */
	if (ptr == NULL)
	    return(NO_MEMORY);
	mp->cmd_text[i] = ptr;
    }

    ptr = malloc(SCREEN_SIZE + 1); /* allocate space for compressed screen */
    if (ptr == NULL)
	return(NO_MEMORY);
    mp->screen = ptr;

    ptr = malloc(SCREEN_SIZE + 1); /* allocate space for uncompressed screen */
    if (ptr == NULL)
	return(NO_MEMORY);
    scr_work = ptr;

    expand_off();	/*; turn off function key expansion */
    expand_off();

	  /*  decode the command tail */

    ret = M12_OPENOLD;		/* default place to start */
    if (argc == 2)
    {
	i = 0;			/* good args, move file name */
	j = 0;
	while (m1_name[i++] = *(argv[1] + j++));
    }
    ret = med_12(ret);		/* call file opener */
    return(ret);
}

clean_up()			    /* clean up and exit */
{
    close(m1_fd);		    /* close the menu file */
    scr_beg();
    clr_scr(cur_attr[SP5_A]);	    /* clear screen */
    scr_end();
    set_attr(SP5_A);		    /* reset the screen attribute */
    expand_on();		/*; turn on function key expansion */
    wrap_on();			/*;*/

    pcursor(0,0);		    /* cursor home */
    exit(SUCCESS);		    /* exit program */
}
                                                                                                                                                                                                