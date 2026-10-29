/*     CMEDMAIN.C  - Copy Menu Utility					    */

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */
/*	Last mode: 8 MAR 85...						    */
/*	Add support for serial terminals				    */
/*	New source lines marked by /*;					    */

#define	MAIN		/*; for fkeys.h */
/*** INCLUDE FILES **********************************************************/

#include <stdio.h>
#include "menu.h"
#include "fkeys.h"
#include "iosubs.h"
#include "attr.h"
#include "scrsubs.h"
#include <ctype.h>

/*** DEFINES ***************************************************************/

#define USER_EXIT   2		/* return code for user requested exit */
#define NO_MEMORY   3		/* No memory available return from init */
#define NO_TERM_DATA 5		/*; No TERM.DAT file located */

/*  defines for calling WM_PK (peek & poke to vc_)  */

#define PEEK	    0
#define POKE	    1
#define CUR_TYPE    62			/* current display type index */
#define MONO_TYPE   0x09		/* mono type value */
#define	CRT_SEG     24			/* video buff. seg in vc_ */
#define MONO_SEG    0xB000		/*;*/
#define COLOR_SEG   0xB800		/*;*/

/*  Defines for copy screen 1 functions */

#define C1_GET_NAMES	1
#define C1_OPEN_SRCE	2
#define C1_ERR_SRCE	3
#define C1_NO_SRCE	4
#define C1_OPEN_DEST	5
#define C1_ERR_DEST	6
#define C1_NO_DEST	7
#define C1_DONE 	8

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

EXTERN	BOOLEAN cmed_01();	     /* in medscr1.c */
EXTERN	BOOLEAN cmed_02();
EXTERN	BOOLEAN cmed_03();

EXTERN	VOID	WM_PK();	    /* in WWCALL.A86 */

/*** EXTERNAL VARIABLES ****************************************************/

/*** GLOBAL VARIABLES ******************************************************/

GLOBAL	BYTE	*src_dir;		    /* the source directory */
GLOBAL	BYTE	*dst_dir;		    /* the destination directory */
GLOBAL	WORD	src_rec[DIRCOUNT];	    /* pointers to start of menus     */
GLOBAL	WORD	dst_rec[DIRCOUNT];	    /* pointers to start of menus     */

/*; thx IH...want strings below to be spaces, not tabs */
GLOBAL	BYTE	m1_name[16] = { "               " };  /* srce menu file name */
GLOBAL	BYTE	m2_name[16] = { "               " }; /* dest menu file name   */
GLOBAL	WORD	m1_fd;			    /* source menu file fd	      */
GLOBAL	WORD	m2_fd;			    /* destination menu file fd       */
GLOBAL	struct	menu	*mp;		    /* the menu structure */

/*; keyboard redirection: */
GLOBAL	struct	f_keys	squid_keys = {
		0xBB, 0xBC, 0xBD, 0xBE, 0xBF,	/*; F1-F5 */
		0xC0, 0xC1, 0xC2, 0xC3, 0xC4,	/*; F6-F10 */
		0xC7, 0xCF			/*; HOME, END */
	};					/*;*/
GLOBAL	struct	f_keys	ser_keys = {
		01,02,				/*; cntl a, cntl b */
		16,17,18,19,20,21,22,23,	/*; cntl p - cntl w */
		03,				/*; HOME = cntl c */
		14				/*; END = cntl n */
	};					/*;*/
GLOBAL	struct	f_keys	*key_ptr = &squid_keys;	/*; for serial vs. pc */

/*** Other Static Variables *************************************************/

MLOCAL	struct	menu	the_menu;	     /* menu storeage	    */

/*** MAIN FUNCTION *********************************************************/

/*	data area for decoding the command tail */

#define NONE	0	    /* possible values for menu_list_spec */
#define ALL	1
#define LIST	2

MLOCAL	BOOLEAN src_spec = FALSE;	 /* source file name specified? */
MLOCAL	BOOLEAN dst_spec = FALSE;	 /* dest file name specified? */
MLOCAL	WORD	menu_list_spec = NONE;	/* menu list specified */
MLOCAL	BYTE	*name_list[100];	/* list of names specified */
MLOCAL	WORD	lst_cnt = -1;		/* number of items in list */

main(argc, argv)

	WORD	argc;
	BYTE	*argv[];
{
	WORD	i;			/* temp counter */
	WORD	ret;			/* return code */
	BOOLEAN edit_more;		/* done with edit */

EXTERN	BYTE	*cur_attr;	/* current attribute table */

/*  Screen Messages */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg cmu_99c[];
EXTERN	WORD	cmuc_99c;


/*;    if(__BDOS(C_GET,0x0) > 3){				*/
/*;	printf("\nCOPYMENU cannot run on this terminal\n");	*/
/*;	exit(-1);						*/
/*;    }							*/

    ret = init(argc, argv);	    /* initialize for edit */
    if (ret == NO_MEMORY)	    /* if initialization fails, */
    {
	scr_beg();		    /* clear the screen */
	clr_scr(cur_attr[DEF_A]);   /* with default attribute */
	p_msg(&title);		    /* print the title */
	p_msgs(cmu_99c, cmuc_99c); /* no memory abort message */
	scr_end();
	any_key();		    /* any character */
	clean_up();		    /* abort */
    }
    if (ret == USER_EXIT)
	clean_up();		    /* user exit requested */
    if (ret == NO_TERM_DATA) {					/*;*/
	printf("\nCOPYMENU cannot run on this terminal.\n");	/*;*/
/*;	clean_up();		because we don't know scrn codes   */
	exit(-1);						/*;*/
    }								/*;*/

    if (src_spec == TRUE && dst_spec == TRUE)	/* Open the menu files */
	ret = cmed_01(C1_OPEN_SRCE);
    else
	ret = cmed_01(C1_GET_NAMES);
    if (ret == USER_EXIT)
	clean_up();
    if (menu_list_spec == NONE)
	ret = cmed_02();
    if (menu_list_spec == ALL)
    {
	for (i = 0; i < DIRCOUNT; i++)
	{
	    ret = chk_4_blanks(&src_dir[i * DIRNAMELEN]);   /* see if there */
	    if (ret > 0)
		cmed_03(i);		    /* if so, copy the menu */
	}
    }
    if (menu_list_spec == LIST)
    {
	for (i = 0; i <= lst_cnt; i++)
	{
	    ret = chk_4_blanks(name_list[i]);	/* see if name non blank */
	    if (ret > 0)
	    {
		mp->menu_num = fnd_mnu(src_dir, name_list[i]);	/* find name */
		if (mp->menu_num >= 0)		/* and copy if there */
		    cmed_03(mp->menu_num);
	    }
	}
    }
    clean_up();
}

/*** clean_up - clean every thing up & exit ***********************************/

clean_up()
{
    close(m1_fd);		    /* close the menu file */
    close(m2_fd);		    /* close the menu file */
    scr_beg();
    clr_scr(cur_attr[SP5_A]);	    /* clear screen */
    scr_end();
    expand_on();		    /*;*/
    wrap_on();			    /*;*/
    pcursor(0,0);		    /* home cursor */
    set_attr(SP5_A);		    /* reset the screen attribute */
    exit(SUCCESS);
}

/*** SUB FUNCTIONS *********************************************************/

/*** CHecK for blanks in menu name ******************************************/

/* returns 0 if name is all blanks, 1 if not all blanks */

chk_4_blanks(str)

    BYTE    *str;		    /* string to check */
{
	WORD	i;		    /* temp counter */
	WORD	ret;		    /* return value */

    ret = 0;			    /* assume fail */
    for (i = 0; i < DIRNAMELEN; i++)
    {
	if (*(str + i) == '\0')
	    return(ret);
	if (*(str + i) != ' ')
	    ret = 1;
    }
    return (ret);
}

/*** INITialize for editing a menu *****************************************/

WORD	init(argc, argv)

	WORD	argc;		/* number of arguments specified */
	BYTE	*argv[];	/* argument text */
{
	WORD	ret;		/* return value */
	WORD	i,j;		/* temp counter */
	BYTE	*ptr;		/* temp pointer */
	BYTE	c;		/* temp character */
	WORD	nxt_char;	/* character counter in command tail */
	UWORD	screen_base;	/*; where the PC phys. screen buff. is. */

EXTERN	BOOLEAN v31;		/* version number we are running under */
EXTERN	WORD	vc_number;	/* our virtual console number */
EXTERN	BYTE	*cur_attr;	/* current attribute table */
EXTERN	BYTE	col_attr[];	/* color attribute table */
EXTERN	struct	scr_msg cmu_99a;
EXTERN	WORD	cmuc_99a;
EXTERN	UWORD	ser_term_init();		/*; check for TERM.DAT */
EXTERN	BYTE	sq_msg_1[], sq_msg_last[];	/*; term-spec. msgs */
EXTERN	BYTE	ser_msg_1[], ser_msg_last[];	/*; term_spec. msgs */

    mp = &the_menu;		/* store address of menu */
    wm_init();			/* initialize for direct virtual i/o */

/**********  set up the proper cur_attr depending on screen type **********/
/*;********  but first, make sure it's a PC-windowed screen:     **********/
    WM_PK(PEEK, vc_number, CRT_SEG, &screen_base);	/*;*/

    if ((screen_base != COLOR_SEG) && (screen_base != MONO_SEG)) {   /*;*/
	if(ser_term_init(vc_number) == 0xffff) return(NO_TERM_DATA); /*;*/
	else {							/*;*/
	 key_ptr = &ser_keys;					/*;*/
	 (BYTE*)i = & sq_msg_last[0] - & sq_msg_1[0];		/*;*/
	 (BYTE*)j = &ser_msg_last[0] - &ser_msg_1[0];		/*;*/
	 if (i != j) return(NO_TERM_DATA);			/*;*/
	 for (i=0; i<j; i++) sq_msg_1[i] = ser_msg_1[i];	/*; overlay */
	 wrap_on();						/*;*/
	}							/*;*/
    }								/*;*/

    else {							/*;*/
	key_ptr = &squid_keys;					/*;*/
	wrap_off();						/*;*/
    	WM_PK(PEEK, vc_number, CUR_TYPE, &i);   /*; get current display type */
	if (( i & 0X00ff) != MONO_TYPE)	    /*; if not mono, set attr = color */
	 cur_attr = &col_attr[0];				/*;*/
    }								/*;*/

    scr_beg();			/* clear the screen */
    clr_scr(cur_attr[DEF_A]);	/* with default attribute */
    scr_end();

    if (v31 == FALSE)		/* Check System Version, MUST be 3.1 */
    {
	scr_beg();		    /* clear the screen */
	clr_scr(cur_attr[DEF_A]);   /* with default attribute */
	p_msg(&title);		    /* print the title */
	p_msgs(cmu_99a, cmuc_99a); /* not correct version message */
	scr_end();
	any_key();		    /* any character */
	return(USER_EXIT);	    /* init failed */
    }

    src_dir = malloc(DIRSIZE + 1);  /* allocate directory space */
    if (src_dir == NULL)
	return(NO_MEMORY);	/* return if can't get memory */

    dst_dir = malloc(DIRSIZE + 1);  /* allocate directory space */
    if (dst_dir == NULL)
	return(NO_MEMORY);	/* return if can't get memory */

    for (i = 0; i < 16; i++)	/* allocate space for commands */
    {
	ptr = malloc(129);	/* 1 command */
	if (ptr == NULL)
	    return(NO_MEMORY);
	mp->cmd_text[i] = ptr;
    }

    ptr = malloc(1921); 	/* allocate space for compressed screen */
    if (ptr == NULL)
	return(NO_MEMORY);
    mp->screen = ptr;

    expand_off();		/*;*/

    for (i = 0; i < 15; i++)	/* clear out the menu names */
    {
	m1_name[i] = ' ';
	m2_name[i] = ' ';
    }

	  /*  decode the command tail */

    lst_cnt = -1;			    /* number in menu name list */
    menu_list_spec = NONE;		    /* list is empty */
    for (i = 1; i < argc; i++)		    /* look at all arguments */
    {
	switch (i)
	{
	    case 1:	  /* source file name specified */
		j = 0;
		while (m1_name[j] = *(argv[i] + j ) )
		    j++;
		src_spec = TRUE;
		break;

	    case 2:	  /* destination file specified */
			    /* create if required */
		j = 0;
		while (m2_name[j] = *(argv[i] + j ) )
		    j++;
		dst_spec = TRUE;
		{
		    m2_fd = openb(m2_name, 2);	/* try to open */
		    if ( m2_fd >= 0)
		    {
			close (m2_fd);
			break;
		    }

		    /* file doesn't exist, create it */

		    m2_fd = creatb(m2_name, 2); /* create the file */
		    if (m2_fd < 0)
			break;			    /* if we can't, quit */
		    for (j = 0; j < DIRSIZE; j++)   /* clear directory */
			*(dst_dir + j) = ' ';
		    for (j = 0; j < DIRCOUNT; j++)  /* clear rec no table */
			dst_rec[j] = 0;
		    wr_dir(m2_fd, dst_dir, &dst_rec[0]);  /* write dir */
		    close(m2_fd);		    /* close dest file */
		}
		break;

	    case 3:	  /* menu name list specified */
			    /* see if ALL specifiec */
/*; correct ALL to -m */
		if ( ( *(argv[i] + 2) == '\0')			/*;*/
		&&   ( *(argv[i]) == '-')			/*;*/
		&&   ( *(argv[i] + 1) == 'm' || *(argv[i] + 1) == 'M') ) /*;*/
		{
		    menu_list_spec = ALL;	/* its all */
		    break;
		}

	    /* it's not all, must be a list */

		nxt_char = 0;	    /* next character in argument list */
		while (*(argv[i] + nxt_char) != '\0')
		{
		    lst_cnt += 1;		/* increment number of names */
		    menu_list_spec = LIST;	/* it's now officially a list */
		    name_list[lst_cnt] = malloc(DIRNAMELEN + 1);/* name length*/
		    if (name_list[lst_cnt] == NULL)
			return(NO_MEMORY);		/* fail if no memory */
		    j = 0;
		    while ((c = toupper(*(argv[i] + nxt_char))) != '\0' &&
			   c != ',' )
		    {
			*(name_list[lst_cnt] + j) = c;
			j += 1; 			/* incr output ptr */
			nxt_char += 1;			/* and input pointer */
			if ( j == DIRNAMELEN)
			    break;
		    }
		    *(name_list[lst_cnt] + j) = '\0';
		    if (c == '\0')
			break;
		    nxt_char += 1;		    /* skip over ',' */
		}   /* while */
		break;

	    default:	    /* invalid command tail */
		break;
	}   /* switch on argv */

    }	/* for argc */

    return(SUCCESS);
}
                                                                                                                                                                                                                                                                                                           