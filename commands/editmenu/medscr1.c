/*	MEDSCR1.C  - Med Screen drivers (1 of 4)			    */

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */

/*** INCLUDE FILES **********************************************************/

#include <stdio.h>
#include "menu.h"
#include "fkeys.h"
#include "iosubs.h"
#include "attr.h"
#include "scrsubs.h"

/*** DEFINES ***************************************************************/

#define ESCAPE	0x1b			/* ascii Esc char */
#define BELL	0x07			/* ascii bell	  */

#define USER_EXIT   2			/* return value for user exit request */
#define GO_BACK     3			/* back a level return value */

/*  Defines for med screen 0 functions */

#define M0_MAKE_NEW	1
#define M0_CHANGE	2
#define M0_COPY_OLD	3
#define M0_DELETE	4
#define M0_DONE 	5

/*  Defines for med screen 1a functions */

#define M1A_GET_NAME	 1
#define M1A_NEW_MENU	 2
#define M1A_DIR_FULL	 3
#define M1A_DONE	 4

/*  Defines for med screen 1b functions */

#define M1B_GET_NAME	 1
#define M1B_READ_MENU	 2
#define M1B_DEL_MENU	 3
#define M1B_DONE	 4

/*  Defines for med screen 1c functions */

#define M1C_GET_NAME	    1
#define M1C_GET_COPY_NAME   2
#define M1C_NEW_MENU	    3
#define M1C_DIR_FULL	    4
#define M1C_BAD_MENU	    5
#define M1C_DISPLAY	    6
#define M1C_DONE	    7

/*  Defines for med screen 1d functions */

#define M1D_GET_NAME	    1
#define M1D_FIND_MENU	    2
#define M1D_DEL_MENU	    3
#define M1D_DONE	    4

/*  Defines for med screen 3 functions */

#define M3_SELECT	1
#define M3_MENU_SCREEN	2
#define M3_FUNCTIONS	3
#define M3_END_EDIT	4
#define M3_NO_FUNCTIONS 5
#define M3_COPY_MENU	6
#define M3_BAD_MENU	7
#define M3_DIR_FULL	8
#define M3_DISP_DIR	9
#define M3_DONE 	10

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

/*** process MED screen 0 *************************************************/

med_00(mp)

struct	menu	*mp;		    /* the menu structure */
{

	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
	BYTE	c;		    /* temp character */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_00a[];
EXTERN	WORD	medc_00a;

/* Other EXTERNS */

/*  LOCALS */

MLOCAL	WORD	cur_step;			/* current step */

    scr_beg();
    clr_scr(cur_attr[DEF_A]);
    p_msg(&title);
    p_msgs(med_00a, medc_00a);	   /* Enter option    */
    scr_end();

    do
    {
    ret = any_key();
    }
    while (   ret != F2_KEY
	   && ret != F3_KEY
	   && ret != F4_KEY
	   && ret != F5_KEY
	   && ret != ESCAPE );

    if (ret == F2_KEY)
	cur_step = M0_MAKE_NEW;
    if (ret == F3_KEY)
	cur_step = M0_CHANGE;
    if (ret == F4_KEY)
	cur_step = M0_COPY_OLD;
    if (ret == F5_KEY)
	cur_step = M0_DELETE;
    if (ret == ESCAPE)
	return(USER_EXIT);		    /* clean up and exit */

    while (cur_step != M0_DONE)
    {
	switch (cur_step)
	{
	case M0_MAKE_NEW:			/* Make Brand New Menu */
	    ret = med_011(mp);			/* get menu name */
	    if (ret == FAILURE) 		/* if any error, start over */
		break;
	    if (ret == GO_BACK) 		/* go to prior level */
		return(SUCCESS);
	    ret = edit_menu(mp);		/* edit the menu */
	    if (ret == GO_BACK) 		/* ask for menu name again */
		break;
	    return(SUCCESS);			/* done with edit */
	    break;

	case M0_CHANGE:
	    ret = med_012(mp);			/* get menu name */
	    if (ret == FAILURE) 		/* if any error, start over */
		break;
	    if (ret == GO_BACK) 		/* go to prior level */
		return(SUCCESS);
	    ret = edit_menu(mp);		/* edit the menu */
	    if (ret == GO_BACK) 		/* ask for menu name again */
		break;
	    return(SUCCESS);			/* done with edit */
	    break;

	case M0_COPY_OLD:
	    ret = med_013(mp);			/* get menu names */
	    if (ret == FAILURE) 		/* if any error, start over */
		break;
	    if (ret == GO_BACK) 		/* go to prior level */
		return(SUCCESS);
	    ret = edit_menu(mp);		/* edit the menu */
	    if (ret == GO_BACK) 		/* ask for menu names again */
		break;
	    return(SUCCESS);			/* done with edit */
	    break;

	case M0_DELETE:
	    ret = med_014(mp);			/* get menu name */
	    if (ret == FAILURE) 		/* if any error, start over */
		break;
	    if (ret == GO_BACK) 		/* go to prior level */
		return(SUCCESS);
	    return(SUCCESS);			/* done with delete */
	    break;

	}   /* switch */
    }	/* While */
}

/*** process MED screen 011 - get new menu name to build *******************/

med_011(mp)

struct	menu	*mp;		    /* the menu structure */
{

	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_01a[];
EXTERN	struct	scr_msg med_01g[];
EXTERN	struct	scr_msg med_01j[];
EXTERN	WORD	medc_01a;
EXTERN	WORD	medc_01g;
EXTERN	WORD	medc_01j;

/*  Input Fields */

EXTERN	struct	field	medf_01[];	    /* med screen 1a fields */

/* Other EXTERNS */

EXTERN	BYTE	*menu_dir;
EXTERN	WORD	menu_rec[];
EXTERN	WORD	m1_fd;			    /* menu file handle */

/*  LOCALS */

MLOCAL	WORD	temp_num;			/* temp menu number */
MLOCAL	WORD	cur_step;			/* current step */

    for (i = 0; i < 8; i++)			/* clear menu name */
	mp->menu_name[i] = ' ';
    mp->menu_name[8] = '\0';

    cur_step = M1A_GET_NAME;

    while (cur_step != M1A_DONE)
    {
	switch(cur_step)
	{
	    case M1A_GET_NAME:
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(med_01a, medc_01a);     /* Enter menu name */
		scr_end();
		ret = g_field(&medf_01[0], mp->menu_name);   /* get name */
		if (ret == ESCRET)
		    return(GO_BACK);	      /* user wants to back up */
		if (ret == F2RET)
		{
		    med_02();			/* display directory */
		    break;
		}
						/* see if name non-blank */
		i = 0;
		while (mp->menu_name[i])
		    if (mp->menu_name[i++] != ' ')
		    {
			cur_step = M1A_NEW_MENU;
			break;
		    }
		break;

	    case M1A_NEW_MENU:
		temp_num = fnd_mnu(menu_dir, mp->menu_name);
		if (temp_num >= 0)
		{
		    scr_beg();
		    p_msgs(med_01j, medc_01j);		   /* menu exists */
		    scr_end();
		    any_key();
		    return(FAILURE);
		    break;
		}

		clr_mnu(mp);		/* clear the menu */
		mp->menu_num = fnd_mnu(menu_dir, "	  ");	/* find mt dir*/
		if (mp->menu_num < 0)			/* see if dir full */
		{
		    cur_step = M1A_DIR_FULL;
		    break;
		}
		return(SUCCESS);		    /* return for menu edit */
		break;


	    case M1A_DIR_FULL:		 /* no room in directory for new menu */
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(med_01g, medc_01g);	       /* no room */
		scr_end();
		any_key();
		return(FAILURE);
		break;

	    default:			/* just in case */
		prog_err();
		break;

	}   /* switch */
    }	/*  while */
    return(SUCCESS);			     /* menu in core & all ok */
}

/*** process MED screen 012 - get menu name to change **********************/

med_012(mp)

struct	menu	*mp;		    /* the menu structure */
{

	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
	BYTE	c;		    /* temp character */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_01c[];
EXTERN	struct	scr_msg med_01h[];
EXTERN	struct	scr_msg med_01i[];
EXTERN	WORD	medc_01c;
EXTERN	WORD	medc_01h;
EXTERN	WORD	medc_01i;

/*  Input Fields */

EXTERN	struct	field	medf_01[];	    /* med screen 1 fields */

/* Other EXTERNS */

EXTERN	BYTE	*menu_dir;
EXTERN	WORD	menu_rec[];
EXTERN	WORD	m1_fd;			    /* menu file handle */

/*  LOCALS */

MLOCAL	WORD	temp_num;			/* temp menu number */
MLOCAL	WORD	cur_step;			/* current step */

    for (i = 0; i < 8; i++)			/* clear menu name */
	mp->menu_name[i] = ' ';
    mp->menu_name[8] = '\0';

    cur_step = M1B_GET_NAME;

    while (cur_step != M1B_DONE)
    {
	switch(cur_step)
	{
	    case M1B_GET_NAME:
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(med_01c, medc_01c);     /* Enter menu name */
		scr_end();
		ret = g_field(&medf_01[1], mp->menu_name);   /* get name */
		if (ret == ESCRET)
		    return(GO_BACK);		/* user wants to backup */

		if (ret == F2RET)
		{
		    med_02();			/* display directory */
		    break;
		}
						/* see if name non-blank */
		i = 0;
		while (mp->menu_name[i])
		    if (mp->menu_name[i++] != ' ')
		    {
			cur_step = M1B_READ_MENU;
			break;
		    }
		break;

	    case M1B_READ_MENU:
		mp->menu_num = fnd_mnu(menu_dir, mp->menu_name);    /* find */
		if (mp->menu_num < 0)
		{
		    scr_beg();
		    p_msgs(med_01i, medc_01i);		/* menu not found */
		    scr_end();
		    any_key();
		    return(FAILURE);			/* go back */
		    break;
		}
		ret = rd_mnu(m1_fd, mp, menu_rec[mp->menu_num]); /* read it */
		if (ret == FAILURE)
		{
		    scr_beg();
		    p_msgs(med_01h, medc_01h);		/* menu corrupted */
		    scr_end();
		    any_key();
		    cur_step = M1B_DEL_MENU;
		    break;
		}
		return(SUCCESS);
		break;

	    case M1B_DEL_MENU:
		del_mnu(menu_dir, mp->menu_num);    /* delete the menu */
		wr_dir(m1_fd, menu_dir, &menu_rec[0] );
		cur_step = M1B_GET_NAME;
		break;

	    default:			/* just in case */
		prog_err();

	}   /* switch */
    }	/*  while */
    return(SUCCESS);			     /* menu in core & all ok */
}

/*** process MED screen 013 - copy existing menu & edit ********************/

med_013(mp)

struct	menu	*mp;		    /* the menu structure */
{

	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
	BYTE	c;		    /* temp character */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_01b[];
EXTERN	struct	scr_msg med_01f[];
EXTERN	struct	scr_msg med_01g[];
EXTERN	struct	scr_msg med_01h[];
EXTERN	struct	scr_msg med_01i[];
EXTERN	struct	scr_msg med_01j[];
EXTERN	WORD	medc_01b;
EXTERN	WORD	medc_01f;
EXTERN	WORD	medc_01g;
EXTERN	WORD	medc_01h;
EXTERN	WORD	medc_01i;
EXTERN	WORD	medc_01j;

/*  Input Fields */

EXTERN	struct	field	medf_01[];	    /* med screen 1 fields */

/* Other EXTERNS */

EXTERN	BYTE	*menu_dir;
EXTERN	WORD	menu_rec[];
EXTERN	WORD	m1_fd;			    /* menu file handle */

/*  LOCALS */

MLOCAL	BYTE	temp_name[] = { "12345678" };
MLOCAL	WORD	temp_num;			/* temp menu number */
MLOCAL	WORD	cur_step;			/* current step */
	WORD	next_step;			/* next step */

    for (i = 0; i < 8; i++)			/* clear menu name */
    {
	mp->menu_name[i] = ' ';
	temp_name[i] = ' ';
    }
    mp->menu_name[8] = '\0';
    temp_name[8] = '\0';

    cur_step = M1C_DISPLAY;
    next_step = M1C_GET_NAME;

    while (cur_step != M1C_DONE)
    {
	switch(cur_step)
	{
	    case M1C_DISPLAY:
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(med_01b, medc_01b);     /* Enter menu names */
		putcbox(&medf_01[2],mp->menu_name); /* new name */
		putcbox(&medf_01[3],temp_name);     /* copy name */
		scr_end();
		cur_step = next_step;
		break;

	    case M1C_GET_NAME:
		ret = g_field(&medf_01[2], mp->menu_name);   /* get new name */
		if (ret == ESCRET)
		    return(GO_BACK);		/* user wants to go back */
		if (ret == F2RET)
		{
		    med_02();			/* display directory */
		    next_step = cur_step;
		    cur_step = M1C_DISPLAY;
		    break;
		}
		i = 0;
		while (mp->menu_name[i])
		    if (mp->menu_name[i++] != ' ')
			cur_step = M1C_GET_COPY_NAME;
		if (cur_step == M1C_GET_COPY_NAME)
		{
		    temp_num = fnd_mnu(menu_dir, mp->menu_name);
		    if (temp_num >= 0)
		    {
			scr_beg();
			p_msgs(med_01j, medc_01j);	       /* menu exists */
			scr_end();
			any_key();
			return(FAILURE);
			break;
		    }
		}
		break;

	    case M1C_GET_COPY_NAME:
		ret = g_field(&medf_01[3], temp_name);	 /* get copy name */
		if (ret == ESCRET)
		    return(GO_BACK);		    /* user wants to go back */
		if (ret == F2RET)
		{
		    med_02();			/* display directory */
		    next_step = cur_step;	/* redisplay the screen */
		    cur_step = M1C_DISPLAY;
		    break;
		}
		i = 0;
		while (temp_name[i])
		    if (temp_name[i++] != ' ')
		    {
			cur_step = M1C_NEW_MENU;
			break;
		    }
		break;

	    case M1C_NEW_MENU:
		clr_mnu(mp);		/* clear the menu */
		mp->menu_num = fnd_mnu(menu_dir, "	  ");	/* find mt dir*/
		if (mp->menu_num < 0)			/* see if dir full */
		{
		    cur_step = M1C_DIR_FULL;
		    break;
		}
					    /* read the menu to copy */
		temp_num = fnd_mnu(menu_dir, temp_name); /* find the menu */
		if (temp_num < 0)
		{
		    scr_beg();
		    p_msgs(med_01f, medc_01f);	    /* menu not found */
		    scr_end();
		    any_key();
		    return(FAILURE);		    /* start over */
		    break;
		}
		ret = rd_mnu(m1_fd, mp, menu_rec[temp_num]);	/* read menu */
		if (ret == FAILURE)
		{
		    mp->menu_num = temp_num;	    /* set menu number to bad */
		    cur_step = M1C_BAD_MENU;
		    break;
		}
		return(SUCCESS);

	    case M1C_DIR_FULL:		 /* no room in directory for new menu */
		scr_beg();
		p_msgs(med_01g, medc_01g);	       /* no room */
		scr_end();
		any_key();
		return(FAILURE);
		break;

	    case M1C_BAD_MENU:		 /* error reading menu, zap it */
		scr_beg();
		p_msgs(med_01h, medc_01h);     /* menu corrupted */
		scr_end();
		any_key();
					/* delete the menu */
		del_mnu(menu_dir, mp->menu_num);
		wr_dir(m1_fd, menu_dir, &menu_rec[0] );
		return(FAILURE);
		break;

	    default:			/* just in case */
		prog_err();

	}   /* switch */
    }	/*  while */
    return(SUCCESS);			     /* menu in core & all ok */
}

/*** process MED screen 014 - delete menu **********************************/

med_014(mp)

struct	menu	*mp;		    /* the menu structure */
{

	WORD	ret;		    /* temp */
	WORD	i;		    /* temp */
	BYTE	c;		    /* temp character */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_01d[];
EXTERN	struct	scr_msg med_01e[];
EXTERN	struct	scr_msg med_01i[];
EXTERN	WORD	medc_01d;
EXTERN	WORD	medc_01e;
EXTERN	WORD	medc_01i;

/*  Input Fields */

EXTERN	struct	field	medf_01[];	    /* med screen 1 fields */

/* Other EXTERNS */

EXTERN	BYTE	*menu_dir;
EXTERN	WORD	menu_rec[];
EXTERN	WORD	m1_fd;			    /* menu file handle */

/*  LOCALS */

MLOCAL	BYTE	temp_char[2] = { "Y" }; 	/* temp 1 character field */
MLOCAL	WORD	temp_num;			/* temp menu number */
MLOCAL	WORD	cur_step;			/* current step */

    for (i = 0; i < 8; i++)			/* clear menu name */
	mp->menu_name[i] = ' ';
    mp->menu_name[8] = '\0';

    cur_step = M1D_GET_NAME;

    while (cur_step != M1D_DONE)
    {
	switch(cur_step)
	{
	    case M1D_GET_NAME:
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(med_01d, medc_01d);     /* Enter menu name */
		scr_end();
		ret = g_field(&medf_01[4], mp->menu_name);   /* get name */
		if (ret == ESCRET)
		    return(GO_BACK);		/* user wants to go back */

		if (ret == F2RET)
		{
		    med_02();			/* display directory */
		    break;
		}
		i = 0;
		while (mp->menu_name[i])
		    if (mp->menu_name[i++] != ' ')
		    {
			cur_step = M1D_FIND_MENU;
			break;
		    }
		break;

	    case M1D_FIND_MENU:
		mp->menu_num = fnd_mnu(menu_dir, mp->menu_name);    /* find */
		if (mp->menu_num < 0)
		{
		    scr_beg();
		    p_msgs(med_01i, medc_01i);	   /* Menu not found  */
		    scr_end();
		    any_key();
		    return(FAILURE);
		}
		scr_beg();
		p_msgs(med_01e, medc_01e);     /* Delete this menu? */
		scr_end();
		temp_char[0] = 'Y';		/* set default to 'Y' */
		ret = g_field(&medf_01[5], temp_char);	 /* get Y or N */
		if (ret == ESCRET)		/* Esc to back up */
		    return(FAILURE);
		if (temp_char[0] == 'Y')
		{
		    cur_step = M1D_DEL_MENU;
		    break;
		}
		if (temp_char[0] != 'N')
		    break;
		else
		    return(SUCCESS);
		break;

	    case M1D_DEL_MENU:
		del_mnu(menu_dir, mp->menu_num);    /* delete the menu */
		wr_dir(m1_fd, menu_dir, &menu_rec[0] );
		return(SUCCESS);
		break;

	    default:			/* just in case */
		prog_err();

	}   /* switch */
    }	/*  while */
    return(SUCCESS);			     /* menu in core & all ok */
}
/*** process MED screen 2 - display menu directory ************************/

med_02()

{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_02a[];
EXTERN	WORD	medc_02a;

/* Other EXTERNS */

EXTERN	BYTE	*menu_dir;	    /* the directory */

/*  temps */

	WORD	col,line,i;

    scr_beg();
    clr_scr(cur_attr[DEF_A]);		    /* clear the screen */
    p_msg(&title);			    /* print screen title */
    i = 0;				    /* index into dir array */
    for (col = 6; col < 70; col += 15)	    /* column loop */
    {
	for (line = 2; line <= 21; line += 1)	    /* line loop */
	{
	    pstr(menu_dir + i, col, line, DIRNAMELEN, BKG_A ); /* send entry */
	    i += DIRNAMELEN;
	}
    }
    p_msgs(med_02a, medc_02a);	/* send [ANY KEY] message */
    scr_end();
    any_key();			/* wait for any key */
    return;
}

/*** process MED screen 3 *************************************************/

/*** program logic error, MAKE MENU abort *********************************/

prog_err()
{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_12f[];
EXTERN	WORD	medc_12f;

    scr_beg();
    clr_scr(cur_attr[DEF_A]);
    p_msg(&title);
    p_msgs(med_12f, medc_12f);	   /* program logic error */
    scr_end();
    any_key();
    clean_up(); 		    /* abort */
}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   