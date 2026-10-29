/*	CMEDSCR1.C  - Copy Menus Screen drivers (1 of 1)

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */
/*;	Last mod: 8 MAR 85...JMB					*/
/*;	serial terminal support						*/
/*;	new source lines marked by /*;					*/

/*** INCLUDE FILES **********************************************************/

#include <stdio.h>
#include "menu.h"
#include "fkeys.h"
#include "iosubs.h"
#include "attr.h"
#include "scrsubs.h"

/*** DEFINES ***************************************************************/

#define USER_EXIT   2			/* return value for user exit request */
#define READWRITE   2			/* for openb */

/*  Defines for copy screen 1 functions */

#define C1_GET_NAMES	1
#define C1_OPEN_SRCE	2
#define C1_ERR_SRCE	3
#define C1_NO_SRCE	4
#define C1_OPEN_DEST	5
#define C1_ERR_DEST	6
#define C1_NO_DEST	7
#define C1_DONE 	8

/*** STRUCTURE DECLARATIONS ************************************************/

/*** EXTERNAL FUNCTION DECLARATIONS ****************************************/


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

EXTERN	VOID	wm_sync();	    /* in wmsubs.c */

EXTERN	VOID	p_msg();	    /* in scrsubs.c */
EXTERN	VOID	p_msgs();
EXTERN	VOID	scr_beg();
EXTERN	VOID	scr_end();
EXTERN	VOID	clr_scr();

EXTERN	WORD	g_field();	    /* in iosubs.c */
EXTERN	WORD	getcbox();
EXTERN	WORD	putcbox();
EXTERN	VOID	any_key();

/*** EXTERNAL VARIABLES ****************************************************/

/*** GLOBAL VARIABLES ******************************************************/

/*** SUB FUNCTIONS *********************************************************/

/*** INITialize for editing a menu *****************************************/

/*** process CMED screen 1 *************************************************/

cmed_01(cur_step)

	WORD	cur_step;	    /* current step number */

{
	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
	BYTE	c;		    /* temp character */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */
EXTERN	WORD	m1_fd;		    /* source file number */
EXTERN	WORD	m2_fd;		    /* destination file number */
EXTERN	BYTE	m1_name[];	    /* source file name */
EXTERN	BYTE	m2_name[];	    /* destination file name */
EXTERN	BYTE	*src_dir;	    /* source file directory */
EXTERN	BYTE	*dst_dir;	    /* destination file directory */
EXTERN	WORD	src_rec[];	    /* source pointers to menus */
EXTERN	WORD	dst_rec[];	    /* destination pointers to menus */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg cmu_01a[];
EXTERN	struct	scr_msg cmu_01b[];
EXTERN	struct	scr_msg cmu_01c[];
EXTERN	struct	scr_msg cmu_01d[];
EXTERN	struct	scr_msg cmu_01e[];
EXTERN	struct	scr_msg cmu_99b[];
EXTERN	WORD	cmuc_01a;
EXTERN	WORD	cmuc_01b;
EXTERN	WORD	cmuc_01c;
EXTERN	WORD	cmuc_01d;
EXTERN	WORD	cmuc_01e;
EXTERN	WORD	cmuc_99b;

/*  Input Fields */

EXTERN	struct	field	cmuf_01[];	    /* cmed screen 1 fields */

/*  LOCALS */

	WORD	cur_fld;			/* current field */
	BOOLEAN src_open;
	BOOLEAN dst_open;

    cmu_01a[1].text = m1_name;		       /* set pointer to file name */
    cmu_01b[2].text = m1_name;		       /* set pointer to file name */
    cmu_01d[2].text = m1_name;		       /* set pointer to file name */

    cmu_01a[3].text = m2_name;		       /* set pointer to file name */
    cmu_01c[2].text = m2_name;		       /* set pointer to file name */
    cmu_01e[2].text = m2_name;		       /* set pointer to file name */

    src_open = FALSE;
    dst_open = FALSE;

    while (src_open == FALSE || dst_open == FALSE)
    {
	switch(cur_step)
	{
	    case C1_GET_NAMES:
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(cmu_01a, cmuc_01a);	/* Enter menu name */
		scr_end();
		cur_fld = 0;			/* start with source file */
		do
		{
		if (src_open == TRUE)
		    cur_fld = 1;
		else
		    if (dst_open == TRUE)
			cur_fld = 0;
		ret = g_field(&cmuf_01[cur_fld],
			      cmu_01a[cur_fld * 2 + 1].text );
		if (ret == RETBIT || ret == ATENDBIT || ret == TABBIT)
		    cur_fld += 1;
		else
		    cur_fld -= 1;

		if (cur_fld > 1)
		    cur_fld = 0;
		if (cur_fld < 0)
		    cur_fld = 1;
		}
		while (ret != F10RET && ret != ESCRET);

		if (ret == ESCRET)
		    return(USER_EXIT);		/* user wants to quit */

		cur_step = C1_OPEN_SRCE;	/* must be F10RET */
		break;

	    case C1_OPEN_SRCE:			/* open the source file */
		if (src_open == TRUE)
		{
		    cur_step = C1_OPEN_DEST;
		    break;
		}
		m1_fd = openb(m1_name, READWRITE);  /* open the file */
		if (m1_fd < 0)
		{
		    cur_step = C1_NO_SRCE;	/* can't open source */
		    break;
		}
		ret = rd_dir(m1_fd, src_dir, &src_rec[0]);  /* read directory */
		if (ret == SUCCESS)
		{
		    cur_step = C1_OPEN_DEST;
		    src_open = TRUE;
		}
		else
		{
		    cur_step = C1_ERR_SRCE;
		    src_open = FALSE;
		}
		break;

	    case C1_ERR_SRCE:			/* source corrupted */
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(cmu_01b, cmuc_01b);     /* File corrupted */
		scr_end();
		any_key();
		cur_step = C1_OPEN_DEST;
		break;

	    case C1_NO_SRCE:			/* source file not found */
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(cmu_01d, cmuc_01d);     /* File not found */
		scr_end();
		any_key();
		cur_step = C1_OPEN_DEST;
		break;

	    case C1_OPEN_DEST:			/* open the destination file */
		if (dst_open == TRUE)
		{
		    cur_step = C1_GET_NAMES;
		    break;
		}
		m2_fd = openb(m2_name, READWRITE);  /* open the file */
		if (m2_fd < 0)
		{
		    cur_step = C1_NO_DEST;	/* can't open dest */
		    break;
		}
		ret = rd_dir(m2_fd, dst_dir, &dst_rec[0]);  /* read directory */
		if (ret == SUCCESS)
		{
		    cur_step = C1_GET_NAMES;
		    dst_open = TRUE;
		}
		else
		{
		    cur_step = C1_ERR_DEST;
		    dst_open = FALSE;
		}
		break;

	    case C1_ERR_DEST:			/* destination file corrupted */
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(cmu_01c, cmuc_01c);     /* File corrupted */
		scr_end();
		any_key();
		cur_step = C1_GET_NAMES;
		break;

	    case C1_NO_DEST:			/* destination file not found */
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(cmu_01e, cmuc_01e);     /* File not found */
		scr_end();
		any_key();
		cur_step = C1_GET_NAMES;
		break;


	    default:			/* just in case */
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(cmu_99b, cmuc_99b);     /* program logic error */
		scr_end();
		any_key();
		return(USER_EXIT);		/* abort */
		break;

	}   /* switch */
    }	/*  while */
    return(SUCCESS);			     /* both files open & all ok */
}

/*** process CMED screen 2 *************************************************/

BOOLEAN cmed_02()

{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg cmu_02a[];
EXTERN	struct	scr_msg cmu_02b[];
EXTERN	WORD	cmuc_02a;
EXTERN	WORD	cmuc_02b;

/* Other EXTERNS */

EXTERN	BYTE	*src_dir;	   /* the directory */

/*  temps */

	WORD	col,line,i,j,ret;	    /* temps */
	WORD	menu_num;		    /* current menu number */
	BYTE	x_array[DIRCOUNT + 1];	    /* user puts X's here */
	BYTE	b_array[DIRCOUNT + 1];	    /* has an 'X' if non-blank dir */
	BOOLEAN found_one;		    /* any non-empty directory entries*/

    for (i = 0; i < DIRCOUNT; i++)	    /* clear temp arrays */
    {
	x_array[i] = ' ';
	b_array[i] = ' ';
    }

    found_one = FALSE;
    scr_beg();
    clr_scr(cur_attr[DEF_A]);		    /* clear the screen */
    p_msg(&title);			    /* print screen title */
    i = 0;				    /* index into dir array */
    menu_num = 0;			    /* current menu number */
    for (col = 6; col < 70; col += 15)	    /* column loop */
    {
	for (line = 2; line <= 21; line += 1)	    /* line loop */
	{
	    for (j = 0; j < DIRNAMELEN; j++)
		if (*(src_dir + i + j) != ' ')
		{
		    b_array[menu_num] = 'X';
		    found_one = TRUE;
		    pstr(src_dir + i, col, line, DIRNAMELEN, BKG_A );
		    pstr(" ", col - 4, line, 1, MOD_A);
		}
	    i += DIRNAMELEN;
	    menu_num += 1;
	}
    }
    p_msgs(cmu_02a, cmuc_02a);	/* send options message */
    scr_end();

	/*  Now allow the user to select the menu's to copy */

    if (found_one == FALSE)
    {
	scr_beg();
	clr_scr(cur_attr[DEF_A]);
	p_msg(&title);
	p_msgs(cmu_02b, cmuc_02b);     /* no menu's found */
	scr_end();
	any_key();
	return(USER_EXIT);		/* abort */
    }

    menu_num = 0;		    /* start at upper left */
    do
    {
	if (menu_num >= DIRCOUNT)
	    menu_num = 0;
	if (menu_num < 0)
	    menu_num = DIRCOUNT - 1;

	while (b_array[menu_num] == ' ')     /* skip to non-blank entry */
	{
	    menu_num += 1;
	    if (menu_num >= DIRCOUNT)
		menu_num = 0;
	}
	line = menu_num % 20 + 2;	/* line number on screen */
	col = 2 + 15 * (menu_num / 20); /* column on screen */
	pcursor(col,line);		/* position cursor */
	set_attr(INP_A);		/* set attribute to input */
	putc_1(x_array[menu_num]);	/*; print current value */
	pcursor(col,line);		/* reposition cursor */
	ret = getraw(); 		/* allow user input */
	if (ret == 'x')
	    ret = 'X';
	if (ret == 'X' || ret == ' ')	/* if X or blank, store */
	    x_array[menu_num] = ret;
	set_attr(MOD_A);		/* set attribute back to modifiable */
	putc_1(x_array[menu_num]);	/*; print the character back */

	if (ret == TAB_KEY || ret == ENTER_KEY || ret == 'X' || ret == ' ')
	    menu_num += 1;
	if (ret == BTAB_KEY)
	{
	    do
	    {
		menu_num -= 1;
		if (menu_num < 0)
		    menu_num = DIRCOUNT - 1;
	    }
	    while (b_array[menu_num] == ' ');
	}

    }	/* do */
    while (ret != ESCAPE && ret != F10_KEY);

    if (ret == F10_KEY)
    {
	for (i = 0; i < DIRCOUNT; i++)
	    if (x_array[i] == 'X')
/*		cmed_03(i);		    /* copy the menu */
/*; IH, must return USER_EXIT if cmed_03 returns it:	     */
		if(cmed_03(i)==USER_EXIT) return(USER_EXIT);
    }
    else
	return (USER_EXIT);

}   /*	cmed_02()   */

/*** process CMED screen 3 ***************************************************/

BOOLEAN cmed_03(menu_num)

	WORD	menu_num;	    /* menu number to copy */
{
	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg cmu_03a[];
EXTERN	struct	scr_msg cmu_03b[];
EXTERN	struct	scr_msg cmu_03c[];
EXTERN	struct	scr_msg cmu_03d[];
EXTERN	WORD	cmuc_03a;
EXTERN	WORD	cmuc_03b;
EXTERN	WORD	cmuc_03c;
EXTERN	WORD	cmuc_03d;

/*  Menu structures etc */

EXTERN	WORD	m1_fd;		    /* source file number */
EXTERN	WORD	m2_fd;		    /* destination file number */
EXTERN	BYTE	*src_dir;	    /* source file directory */
EXTERN	BYTE	*dst_dir;	    /* destination file directory */
EXTERN	WORD	src_rec[];	    /* source pointers to menus */
EXTERN	WORD	dst_rec[];	    /* destination pointers to menus */
EXTERN	struct	menu	*mp;	    /* menu structure pointer */

/*  LOCALS */

MLOCAL	WORD	cur_step;			/* current step */
	BYTE	menu_name[DIRNAMELEN + 1];	/* temporary menu name */
	WORD	dest_menu_num;			/* destination menu index */

    for (i = 0; i < DIRNAMELEN; i++)
	menu_name[i] = *(src_dir + i + DIRNAMELEN * menu_num);
    menu_name[DIRNAMELEN] = '\0';

    cmu_03a[1].text = menu_name;		/* set address in screen msg */

    scr_beg();
    clr_scr(cur_attr[DEF_A]);
    p_msg(&title);
    p_msgs(cmu_03a, cmuc_03a);		    /* paint the screen    */
    scr_end();

    ret = rd_mnu(m1_fd, mp, src_rec[menu_num]);    /* read the menu */
    if (ret == FAILURE)
    {
	scr_beg();
	p_msgs(cmu_03c, cmuc_03c);		/* can't read source   */
	scr_end();
	any_key();
	return (FAILURE);
    }

    dest_menu_num = fnd_mnu(dst_dir, menu_name);    /* find menu in dest */
    if (dest_menu_num < 0)
    {
	dest_menu_num = fnd_mnu(dst_dir, "        ");	/* find empty one */
/*; thx IH...spaces, not tabs */
	if (dest_menu_num < 0)
	{
	    scr_beg();
	    p_msgs(cmu_03b, cmuc_03b);		/* dest direct full, abort? */
	    scr_end();
	    do
	    {
		ret = any_key();		/* get user response */
	    }
	    while (ret != ESCAPE && ret != F10_KEY);

	    if (ret == F10_KEY) 		  /* continue with copy */
		return (FAILURE);
	    else
		return(USER_EXIT);		/* abort copy */

	}   /* no empty dest directory entry	*/
    }	/* menu not in destination */

    /*	have a destination menu entry */

    ret = wr_mnu(m2_fd, mp);			/* write the menu */
    if (ret == 0)
    {
	scr_beg();
	p_msgs(cmu_03d, cmuc_03d);		/* can't write destination */
	scr_end();
	any_key();
	return (FAILURE);
    }

    dst_rec[dest_menu_num] = ret;		/* store the location */
    upd_dir(dst_dir, dest_menu_num, menu_name); /* update directory */
    wr_dir (m2_fd, dst_dir, &dst_rec[0]);	/* write directory */
    return(SUCCESS);				/* return a hero */

}   /* cmed_03() /*
                                                                                                                                                                                                                                                                                                                                                                                                                                                                     