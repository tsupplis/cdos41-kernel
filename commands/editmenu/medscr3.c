/*	MEDSCR3.C  - Med Screen drivers (3 of 4)			    */

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
#define RETKEY	0x0d			/* ascii return */

#define USER_EXIT   2			/* return value for user exit request */
#define GO_BACK     3			/* return value to go to prior step */

/*  Defines for med screen 8 functions */

#define M8_DISPLAY_SCREEN 0
#define M8_GET_FIELD	  1
#define M8_DONE 	  2

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

/*** process MED screen 8 - get ESC and ENTER options, etc ****************/

med_08(mp)

struct	menu	*mp;		    /* the menu structure */
{

	WORD	ret;		    /* temp */
	BYTE	c;		    /* temp character */
	WORD	i;		    /* temp */
EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_08a[];
EXTERN	WORD	medc_08a;

/*  Input Fields */

EXTERN	struct	field	medf_08[];	    /* med screen 8 fields */

/*  LOCALS */

MLOCAL	BYTE	temp_char[] = { "M" };
	WORD	cur_step;		    /* current step */
	WORD	cur_fld;		    /* current input field */
	BYTE	*data[6];		    /* pointer to data fields */

    data[0] = &(mp->esc_enable);
    data[1] = &(mp->enter_enable);
    data[2] = &(mp->save_drive);
    data[3] = &(mp->save_user);
    data[4] = &(mp->save_path);
    data[5] = &(mp->save_map);

    cur_step = M8_DISPLAY_SCREEN;
    while (cur_step != M8_DONE)
    {
	switch(cur_step)
	{
	    case M8_DISPLAY_SCREEN:
		scr_beg();
		clr_scr(cur_attr[DEF_A]);
		p_msg(&title);
		p_msgs(med_08a, medc_08a);     /* Escape & Enter options */
		for (i = 0; i < 4; i++) 	/* changed to 4 */
		    putcbox(&medf_08[i], data[i]);
/*		putcbox(&medf_08[6], &(mp->cmd_types[14]));    /* commands */
/*		putcbox(&medf_08[8], &(mp->cmd_types[15]));		   */
		putcbox(&medf_08[7], mp->cmd_text[14]);
		putcbox(&medf_08[9], mp->cmd_text[15]);
		scr_end();
		cur_step = M8_GET_FIELD;
		cur_fld = 0;
		break;

	    case M8_GET_FIELD:
		if (cur_fld < 0)		    /* make fields circular */
		    cur_fld = 9;
		if (cur_fld > 9)
		    cur_fld = 0;
		if (cur_fld == 4 || cur_fld == 5)   /* skip fields 4 & 5 */
		    cur_fld = 6;

		if (cur_fld < 6)
		{				    /* its a Y/N field */
		    temp_char[0] = *data[cur_fld];
		    do
		    {
			ret = g_field(&medf_08[cur_fld], temp_char);
		    }
		    while (temp_char[0] != 'Y' && temp_char[0] != 'N'
			    && ret != ESCRET && ret != F10RET );
		    if (ret == ESCRET || ret == F10RET )
			return;
		    *data[cur_fld] = temp_char[0];
		    if (ret != BTABRET)
			cur_fld += 1;
		    else
			cur_fld -= 1;
		}   /* if cur_fld < 6 */

		else	/* it's a command line */
		{
		    if (cur_fld % 2 != 0)	    /* odd's are command text */
		    {
			i = (cur_fld - 7) / 2 + 14;	/* command index */
			ret = g_field(&medf_08[cur_fld], mp->cmd_text[i]);
			if (ret == ESCRET || ret == F10RET)
			    return;
		    }
		    else			    /* even's are cmd types */
		    ret = TABRET;		    /* to skip the cmd types */
		    if (0)			    /* to skip cmd types */
		    {
			i = (cur_fld - 6) / 2 + 14;	    /* command index */
			temp_char[0] = mp->cmd_types[i];    /* move to temp */
			do
			{
			    ret = g_field(&medf_08[cur_fld], temp_char );
			}
			while (temp_char[0] != 'A' && temp_char[0] != 'O' &&
			       temp_char[0] != 'C' && temp_char[0] != 'E' &&
			       temp_char[0] != ' ' &&
			       ret != ESCRET	   && ret != F10RET );
			if (ret == ESCRET || ret == F10RET)
			    return;
			mp->cmd_types[i] = temp_char[0];    /* move char back */
		    }	/* else it's even */
		    if (ret != BTABRET)
			cur_fld += 1;
		    else
			cur_fld -= 2;
		    if (ret == BTABRET && cur_fld == 5) /* to skip 4 & 5 */
			cur_fld = 3;
		}   /* else its a command line */
		break;

	    case M8_DONE:		    /* can't get here */
		return(SUCCESS);

	    default:		    /* just in case */
		prog_err();

	}   /* switch */
    }	/*  while */
    return(SUCCESS);
}

/*** process MED screen 9 Function Key Definition Help *********************/

med_09()
{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_09a[];
EXTERN	WORD	medc_09a;

/* Other EXTERNS */

/*  temps */

    scr_beg();
    clr_scr(cur_attr[DEF_A]);	/* clear the screen */
    p_msg(&title);
    p_msgs(med_09a, medc_09a);	/* print the screen */
    scr_end();
    any_key();			/* wait for any key */
    return;
}

/*** process MED screen 10 - Get Function Key Definitions *****************/

VOID	med_10(mp)

struct	menu	*mp;		    /* the menu structure */

{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_10a[];
EXTERN	WORD	medc_10a;

/* input fields */

EXTERN	struct	field	medf_10[];

	BYTE	c;		    /* character temp */
	WORD	cur_fld;	    /* current field number */
	WORD	prior_fld;	    /* save area for cur_fld */
	WORD	ret;
	WORD	i;
MLOCAL	BYTE	tchar[2] = { " " }; /* temp for character entry */


/*	    Get the Fields */

    cur_fld = 99;
    prior_fld = 1;
    while (cur_fld)
    {
    if (cur_fld == 99)
	{
	    scr_beg();
	    clr_scr(cur_attr[DEF_A]);
	    p_msg(&title);
	    p_msgs(med_10a, medc_10a);	    /* The screen */
	    for (i = 0; i < 10; i++)	    /* print the commands & types */
	    {
		medf_10[0].upper = i * 2 + 2;		    /* set upper line */
		medf_10[0].lower = i * 2 + 3;		    /* set lower line */
		putcbox(&medf_10[0], mp->cmd_text[i]);	    /* print command */

		medf_10[1].upper = i * 2 + 2;		    /* set upper line */
		medf_10[1].lower = i * 2 + 2;		    /* set lower line */
		putcbox(&medf_10[1], &(mp->cmd_types[i]));  /* print cmd type */
	    }
	    scr_end();
	    cur_fld = prior_fld;
	    continue;
	}   /* if cur_fld = 99 */

	if (cur_fld % 2 == 0)		/* even numbers are commands */
	{
	    i = (cur_fld - 2) / 2;	    /* command index */
	    if (mp->cmd_types[i] == 'M')    /* set proper field type */
		medf_10[0].type = 1;
	    else
		medf_10[0].type = 0;
	    medf_10[0].upper = cur_fld; 	/* set upper line */
	    medf_10[0].lower = cur_fld + 1;	/* set lower line */
	    ret = g_field(&medf_10[0], mp->cmd_text[i]);
	}
	else				/* odd numbers are command types */
	{
	    medf_10[1].upper = cur_fld + 1;	/* set upper line */
	    medf_10[1].lower = cur_fld + 1;	/* set lower line */
	    i = (cur_fld - 1) / 2;		/* command index */
	    tchar[0] = mp->cmd_types[i];	/* move to temp */
	    do
		ret = g_field(&medf_10[1], tchar );
	    while (tchar[0] != 'A' && tchar[0] != 'O' &&
		   tchar[0] != 'M' && tchar[0] != 'C' &&
		   tchar[0] != 'E' && tchar[0] != ' ' );
	    mp->cmd_types[i] = tchar[0];	/* move char back */
	}
	if (ret == ESCRET)			/* backup */
	    return(GO_BACK);

	if (ret == F1RET)			/* help */
	{
	    med_09();
	    prior_fld = cur_fld;
	    cur_fld = 99;
	    continue;
	}
	if (ret == F2RET)			/* ENTER & ESC options */
	{
	    med_08(mp);
	    prior_fld = cur_fld;
	    cur_fld = 99;
	    continue;
	}

	if (ret == F10RET)
	    return;
	if (ret == TABRET || ret == RETRET || ret == ATENDRET )
	    cur_fld += 1;
	else
	    cur_fld -= 1;
	if (cur_fld < 1)
	    cur_fld = 20;
	if (cur_fld > 20)
	    cur_fld = 1;
    }	/* while */

}   /* med_10() /*

/*** process MED screen 11 ************************************************/

WORD	med_11()
{
	BYTE	temp_char[2];	    /* temp character for input */
	WORD	ret;		    /* temp */

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_11a[];
EXTERN	WORD	medc_11a;

/*  input fields */

EXTERN	struct	field	medf_11[];

    scr_beg();
    clr_scr(cur_attr[DEF_A]);
    p_msg(&title);
    p_msgs(med_11a, medc_11a);	    /* The screen */
    scr_end();
    temp_char[0] = 'Y'; 	    /* set default = Y to save */
    temp_char[1] = '\0';	    /* terminate string */
    do
    {
	ret = g_field(&medf_11[0], temp_char);
	if (ret == ESCRET)
	    return(GO_BACK);
    }
    while (temp_char[0] != 'Y' && temp_char[0] != 'N');
    if (temp_char[0] == 'Y')
	return(SUCCESS);
    return(FAILURE);

}   /* med_11() /*
                                                                                                                                                                                                                                                                                                                                                                                                                                                                              