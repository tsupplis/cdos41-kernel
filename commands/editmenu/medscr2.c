/*	MEDSCR2.C  - Med Screen drivers (2 of 4)			    */

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */

/*** INCLUDE FILES **********************************************************/

#include <stdio.h>
#define	 putchar_1(c)	putc_1(c,stdout)
#include "menu.h"
#include "fkeys.h"
#include "iosubs.h"
#include "attr.h"
#include "scrsubs.h"

/*** DEFINES ***************************************************************/

#define USER_EXIT   2			/* return value for user exit request */
#define GO_BACK     3			/* return value to backup 1 step */

/*  Defines for med screen 4 functions */

#define M4_GET_SCREEN	 0
#define M4_HELP 	 1
#define M4_ATTR_SELECT	 2
#define M4_SELECT_COLOR  3

#define M4_INSERT	 5
#define M4_DELETE	 6
#define M4_CENTER	 7
#define M4_COPY 	 8
#define M4_COPY_GET	 9
#define M4_COPY_VALIDATE 10
#define M4_COPY_DO_IT	 11
#define M4_SHOW_CURSOR	 12
#define M4_DISPLAY	 13
#define M4_SPECIAL	 14
#define M4_SPECIAL_DO	 15
#define M4_MOVE_OPT	 16
#define M4_DONE 	 17

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

/*** process MED screen 4 - Define the Menu screen ************************/

med_04(mp)

struct	menu	*mp;		    /* the menu structure */
{

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_04a[];
EXTERN	struct	scr_msg med_04b[];
EXTERN	struct	scr_msg med_04c[];
EXTERN	struct	scr_msg med_04d[];
EXTERN	struct	scr_msg med_04e[];
EXTERN	struct	scr_msg med_04f[];
EXTERN	struct	scr_msg med_04g[];
EXTERN	struct	scr_msg med_04i[];
EXTERN	WORD	medc_04a;
EXTERN	WORD	medc_04b;
EXTERN	WORD	medc_04c;
EXTERN	WORD	medc_04d;
EXTERN	WORD	medc_04e;
EXTERN	WORD	medc_04f;
EXTERN	WORD	medc_04g;
EXTERN	WORD	medc_04i;

/*  Input Fields */

EXTERN	struct	field	medf_04[];	    /* med screen 4 fields */

/* Other EXTERNS */

EXTERN	BYTE	*scr_work;		    /* working screen area */
EXTERN	BYTE	*cur_attr;		    /* current attribute table */
EXTERN	WORD	vc_segment;		    /* segment of virtual screen */

/*  LOCALS */

MLOCAL	BYTE	temp_char[] = { "M" };
	WORD	cur_step;		    /* current step */
	BOOLEAN cursor_pos;		    /* is cursor posn shown? */
	WORD	ret;			    /* temp */
	WORD	i,j,k,s,s1,n;		    /* temp */
MLOCAL	BYTE	tstr[81];		    /* temp string */

	    /* M4_COPY variables */

MLOCAL	WORD	copy_p[3];		    /* numeric versions of parms */
	WORD	cur_fld;		    /* current index of same */
	WORD	src_st; 		    /* source starting byte */
	WORD	src_end;		    /* source end byte */
	WORD	dest_st;		    /* dest start byte */

	    /* M4_SPECIAL variables */

	BYTE	spec_char[161]; 	    /* special character table */
	BYTE	last_char;		    /* current character */
	WORD	col,line;		    /* current cursor position */
	WORD	spec_col_max;		    /* max column, 2nd row */
struct	field	*p;			    /* temp pointer to field struct */

	    /* M4_ATTR_SELECT variables */

	BYTE	c_char; 		    /* select character */
MLOCAL	BYTE	c_color[] = { "kbgrcmyw"};  /* color selectors */
struct	scr_msg *p1;			    /* pointer to scr_msg structure */
	BYTE	*ptr;			    /* just a byte pointer */
	WORD	new_fld;		    /* temp */
	WORD	temp_fld;		    /* temp */
	WORD	atr_fld;		    /* attribute field */
	WORD	col_fld;		    /* color field */

	    /* Variables to relocate options from top to bottom of screen */

	BOOLEAN at_top; 		    /* true of options at top */
	WORD	ln_21;			    /* where line 21 is */
	WORD	ln_22;			    /* where line 22 is */
	WORD	ln_23;			    /* where line 23 is */
	WORD	scr_offset;		    /* offset of 1st char in box */
	WORD	scr_box;		    /* field index of current box */


	    /* M4_SPECIAL initialization */

    for (i = 0; i < 160; i++)		    /* blank the table */
	spec_char[i] = ' ';
    spec_char[160] = '\0';		    /* terminate the string */
    j = 0;				    /* fill in the specials */
    for (i = 1; i < 255; i++)
	if (i != ESCAPE && ( i < ' ' || i > '~' ) && i != 7 && i != 9 )
	    spec_char[j++] = i;
    spec_col_max = j - 80;		    /* maximum column on 2nd row */
    col = 0;				    /* set initial values */
    line = 1;
    last_char = spec_char[0];

	    /* Normal Initialization */

    cursor_pos = FALSE;
    at_top = TRUE;			    /* fake out to start at bottom */
    cur_step = M4_MOVE_OPT;		    /* start with option move */
    expand(mp->screen, scr_work);	    /* expand compressed screen */
    scr_work[SCREEN_SIZE] = '\0';	    /* terminate string */
    medf_04[0].col = 0; 		    /* set cursor column	*/
    medf_04[0].line = 0;		    /* set cursor line		*/
    atr_fld = 0;			    /* attribute starting field */
    col_fld = 0;			    /* color starting field */

    while (cur_step != M4_DONE)
    {
	switch(cur_step)
	{
	    case M4_GET_SCREEN:
		scr_beg();
		clr_scr(cur_attr[SP2_A]);
		p_msgs(med_04a, medc_04a);     /* options */
		if (cursor_pos)
		    p_msgs(med_04e, medc_04e);	/* print cursor posn */
		cursor_pos = FALSE;
/*; thx IH!	putcbox(&medf_04[scr_box], &scr_work[scr_offset]);   screen */
		scr_end();
		ret = getcbox(&medf_04[scr_box], &scr_work[scr_offset]);
		if (ret == CTLZRET)
		    cur_step = M4_MOVE_OPT;	/* move options */
		if (ret == F1RET)
		    cur_step = M4_HELP; 	/* user wants help */
		if (ret == F2RET)
		    cur_step = M4_ATTR_SELECT;	/* attributes */
		if (ret == F3RET)
		    cur_step = M4_INSERT;	/* Insert a line */
		if (ret == F4RET)
		    cur_step = M4_DELETE;	/* Delete a line */
		if (ret == F5RET)
		    cur_step = M4_CENTER;	/* Center a line */
		if (ret == F6RET)
		    cur_step = M4_COPY; 	/* Copy lines */
		if (ret == F7RET)
		    cur_step = M4_SHOW_CURSOR;	/* Show cursor position */
		if (ret == F8RET)
		    cur_step = M4_DISPLAY;	/* Display screen */
		if (ret == F9RET)
		    cur_step = M4_SPECIAL;	/* Enter special characters */
		if (ret == F10RET)
		    cur_step = M4_DONE; 	/* Done with Edit */
		if (ret == ESCRET)
		{
		    scr_beg();
		    p_msgs(med_04b, medc_04b);	   /* abort?  */
		    scr_end();
		    pcursor(med_04b[1].col,med_04b[1].line);
		    do
		    {
			ret = getraw();
		    }
		    while (ret != 'n' && ret != 'N' &&
			   ret != 'y' && ret != 'Y' && ret != ENTER_KEY);
		    if (ret == 'y' || ret == 'Y')
			return(GO_BACK);
		    break;
		}   /* ret == ESCRET */
		break;

	    case M4_MOVE_OPT:
		if (at_top == TRUE)
		{
		    at_top = FALSE;		/* move to bottom */
		    ln_21 = 21;
		    ln_22 = 22;
		    ln_23 = 23;
		    scr_offset = 0;
		    scr_box = 0;
		    medf_04[0].col  = medf_04[4].col;
		    medf_04[0].line = medf_04[4].line;
		    if (medf_04[scr_box].line > 20)  /* make cursor visible */
			medf_04[scr_box].line = 20;
		    if (line == 1)
			line = 22;
		    else
			line = 23;
		}
		else
		{
		    at_top = TRUE;		/* move to top */
		    ln_21 = 0;
		    ln_22 = 1;
		    ln_23 = 2;
		    scr_offset = 3 * 80;
		    scr_box = 4;
		    medf_04[4].col  = medf_04[0].col;
		    medf_04[4].line = medf_04[0].line;
		    if (medf_04[scr_box].line < 3)   /* make cursor visible */
			medf_04[scr_box].line = 3;
		    if (line == 22)
			line = 1;
		    else
			line = 2;
		}
		/* adjust positions of fields on screen */

		p = &medf_04[scr_box];		/* set pointer to field */

		med_04a[0].line = ln_21;	/* options */
		med_04a[1].line = ln_22;
		med_04a[2].line = ln_23;

		for (i = 0; i < 4; i++) 	/* copy lines */
		    med_04c[i].line = ln_21;
		med_04c[4].line = ln_22;
		med_04c[5].line = ln_23;

		med_04d[0].line = ln_21;	/* special chars options */

		for (i = 0; i < medc_04e; i++)	/* cursor position display */
		    med_04e[i].line = ln_21;

		for (i = 0; i < medc_04i; i++)	/* attributes options */
		    med_04i[i].line = ln_21;

		for (i = 0; i < medc_04f; i++)	/* attributes */
		    med_04f[i].line = ln_22;

		for (i = 0; i < medc_04g; i++)	/* colors */
		    med_04g[i].line = ln_23;

		med_04b[0].line = ln_21;	/* abort ? */
		med_04b[1].line = ln_21;	/* answer */
		med_04b[2].line = ln_21;	/* blanks */

		cur_step = M4_GET_SCREEN;
		break;

	    case M4_HELP:
		med_06();
		cur_step = M4_GET_SCREEN;
		break;

	    case M4_ATTR_SELECT:		    /* define screen attr */
/*; ? & of */	ptr = &(scr_work + 80 * p->line + p->col); /* where to store */
/*; ptr.   */	scr_beg();
		clrstr(0, ln_21, 80 * 3, DEF_A); /* clear*/
		p_msgs(med_04f, medc_04f);     /* attributes */
		p_msgs(med_04i, medc_04i);     /* options */
						/* make destination rev video */
		FDRAW(ptr, ( 80 * p->line + p->col ) * 2, 1,
			   rev_vid(cur_attr[SP2_A]) , vc_segment);
		scr_end();
		p = &(medf_04[scr_box]);	/* point to screen field */
		do				/* let user select field */
		{
		    p1 = &(med_04f[atr_fld]);	    /* point to current field */
		    pcursor(p1->col, p1->line);
		    set_attr(SP10_A);
		    printf_x(p1->text);
		    ret = any_key();
		    if (ret == F1_KEY)
		    {
			med_07();			/* attribute help */
			scr_beg();			/* paint the screen */
			clr_scr(cur_attr[DEF_A]);
			putcbox(&medf_04[scr_box], &scr_work[scr_offset]);
			p_msgs(med_04f, medc_04f);     /* attributes */
			p_msgs(med_04i, medc_04i);     /* options */
			scr_end();
			continue;
		    }
		    new_fld = atr_fld;
/*;*/		    if (ret == LEFTARROW_KEY || ret == BS_KEY || ret == '<')
			new_fld = atr_fld - 1;
/*;*/		    if (ret == RIGHTARROW_KEY || ret == SPACE_KEY || ret == '>')
			new_fld = atr_fld + 1;
		    if (new_fld != atr_fld)
		    {
			pcursor(p1->col, p1->line);
			set_attr(p1->attr_ind);
			printf_x(p1->text);
			atr_fld = new_fld;
			if (atr_fld < 0)
			    atr_fld = medc_04f - 1;
			if (atr_fld >= medc_04f)
			    atr_fld = 0;
			if (atr_fld >= medc_04f - 2)	/* color */
			    if (p->col == p->right && p->line == p->lower)
				atr_fld = 0;		/* & last col = no */
		    }
		}   /* do */
		while (ret != ESCAPE && ret != F10_KEY && ret != ENTER_KEY);
		if (ret == ESCAPE)
		{
		    cur_step = M4_GET_SCREEN;
		    break;
		}
		/*  it's F10 - EXECUTE */

		cur_step = M4_GET_SCREEN;
		switch(atr_fld)
		{
		    case 0:		    /* reverse video */
			*ptr = '\\';
			break;

		    case 1:		    /* underscore */
			*ptr = '_';
			break;

		    case 2:		    /* bright */
			*ptr = '}';
			break;

		    case 3:		    /* blink  */
			*ptr = '{';
			break;

		    case 4:		    /* foreground */
			c_char = '~';
			cur_step = M4_SELECT_COLOR;
			break;

		    case 5:		    /* background */
			c_char = '|';
			cur_step = M4_SELECT_COLOR;
			break;

		}   /* switch  atr_fld */
		break;			 /* off to where ever */

	    case M4_SELECT_COLOR:
		scr_beg();
		p_msgs(med_04g, medc_04g);     /* colors */
		scr_end();
		temp_fld = atr_fld;
		p = &(medf_04[scr_box]);	/* point to screen field */
		do				/* let user select field */
		{
		    p1 = &(med_04g[col_fld]);	    /* point to current field */
		    pcursor(p1->col, p1->line);
		    set_attr(SP10_A);
		    printf_x(p1->text);
		    ret = any_key();
		    if (ret == F1_KEY)
		    {
			med_07();			/* attribute help scrn *
			scr_beg();			/* paint the screen */
			clr_scr(cur_attr[DEF_A]);
			putcbox(&medf_04[scr_box], &scr_work[scr_offset]);
			p_msgs(med_04g, medc_04g);     /* colors */
			p_msgs(med_04f, medc_04f);     /* attributes */
			p_msgs(med_04i, medc_04i);     /* options */
			scr_end();
			p1 = &(med_04f[temp_fld]);  /* point to attr field */
			pcursor(p1->col, p1->line);
			set_attr(SP10_A);
			printf_x(p1->text);
			continue;
		    }
		    new_fld = col_fld;
		    if (ret == LEFTARROW_KEY || ret == BS_KEY)
			new_fld = col_fld - 1;
		    if (ret == RIGHTARROW_KEY || ret == SPACE_KEY)
			new_fld = col_fld + 1;
		    if (new_fld != col_fld)
		    {
			pcursor(p1->col, p1->line);
			set_attr(p1->attr_ind);
			printf_x(p1->text);
			col_fld = new_fld;
			if (col_fld < 0)
			    col_fld = medc_04g - 1;
			if (col_fld >= medc_04g)
			    col_fld = 0;
		    }
		}   /* do */
		while (ret != ESCAPE && ret != F10_KEY && ret != ENTER_KEY);
		if (ret == ESCAPE)
		{
		    cur_step = M4_GET_SCREEN;
		    break;
		}
		/*  it's F10 - EXECUTE */

/*; & req'd? */	ptr = &(scr_work + 80 * p->line + p->col); /* where to store */
		*(ptr++) = c_char;		/* store the select */
		*(ptr) = c_color[col_fld];	/* store the color */
		cur_step = M4_GET_SCREEN;
		break;

	    case M4_INSERT:		    /* insert a line at cursor pos */
		s = medf_04[scr_box].line * 80;   /* first char to move */
		if ( s < 1919 - 80 )	    /* only if not last line */
		    for (i = 1919 - 80; i >= s; i--)	/* move chars down */
			*(scr_work + i + 80) = *(scr_work + i);
		for (i = s; i < s + 80; i++)
		    *(scr_work + i) = ' ';   /* clear inserted line */
		cur_step = M4_GET_SCREEN;
		break;

	    case M4_DELETE:		    /* delete line at cursor pos */
		s = medf_04[scr_box].line * 80;     /* first char to zap */
		if ( s < 1919 - 80 )	    /* only if not last line */
		    for (i = s + 80; i <= 1919; i++)
			*(scr_work + i - 80) = *(scr_work + i);
		for (i = 1920 - 80; i <= 1919; i++) /* clear last line */
		    *(scr_work + i) = ' ';
		cur_step = M4_GET_SCREEN;
		break;

	    case M4_CENTER:		    /* center text on current line */
		cur_step = M4_GET_SCREEN;   /* where to return when done */
		s = medf_04[scr_box].line * 80;   /* start of line to center */
		i = s;			    /* find first non-blank char */
		while (*(scr_work + i) == ' ' && i++ < s + 80);
		if (i > s + 79) 	    /* if none, get out */
		    break;
		j = s + 79;		    /* find last non-blank char */
		while (*(scr_work + j) == ' ' && j-- >= s);
		if (j < s || j < i )	    /* if none, get out */
		    break;
		for (k = 0; k < 80; k++)    /* clear temp string */
		    tstr[k] = ' ';
		n = j - i + 1;		    /* number of characters */
		s1 = 40 - n / 2;	    /* start index in destination */
		for (k = s1; k < s1 + n; k++)	/* move to temp */
		    tstr[k] = *(scr_work + i++);
		for (k = 0; k < 80; k++)    /* move back to screen */
		    *(scr_work + s + k) = tstr[k];
		break;

	    case M4_COPY:		    /* copy lines from here to there */
		sprintf(med_04c[1].text, "%02d",	 /* cur line */
			medf_04[scr_box].line + 1);
		sprintf(med_04c[2].text, "%02d",
			medf_04[scr_box].line + 1);
		sprintf(med_04c[3].text, "%02d", 0);	/* no default on dest */
		cur_fld = 3;		    /* start with dest start */
		cur_step = M4_COPY_GET;
		break;

	    case M4_COPY_GET:		    /* copy lines, get fields */
		scr_beg();
		clrstr(0, medf_04[scr_box + 1].upper, 80 * 3, DEF_A); /* clear*/
		p_msgs(med_04c, medc_04c);	/* paint the screen */
		scr_end();
		cur_step = M4_COPY_VALIDATE;	/* normal where we go */

		while (cur_fld)
		{
		    ret = g_field(&medf_04[cur_fld + scr_box],
					med_04c[cur_fld].text );

		    if (ret == F10RET)		/* execute the copy */
			break;

		    if (ret == ESCRET)		/* abort */
		    {
			cur_step = M4_GET_SCREEN;
			break;
		    }

		    if (ret == ATENDRET || ret == TABRET || ret ==  RETRET)
			cur_fld += 1;		/* next field to right */

		    if (ret == BTABRET)
			cur_fld -= 1;		/* next field to left */

		    if (cur_fld > 3)		/* do screen wrap */
			cur_fld = 1;
		    if (cur_fld < 1)
			cur_fld = 3;
		}   /* while (cur_fld) */
		break;

	    case M4_COPY_VALIDATE:	    /* copy lines, validate input */
		cur_step = M4_COPY_DO_IT;   /* normal where we go */

		for (i = 0; i < 3; i++)     /* convert the fields */
		{
		    ret = sscanf(med_04c[i + 1].text, "%d", &copy_p[i]);
		    if (ret < 1)
			cur_step = M4_COPY_GET;
		    if (copy_p[i] < 1 || copy_p[i] > 24)
			cur_step = M4_COPY_GET;
		    copy_p[i] -= 1;	    /* make zero relative */
		}

		if (copy_p[0] > copy_p[1] ||	/* validate the fields */
		    copy_p[1] - copy_p[0] + copy_p[2] > 23)
		    cur_step = M4_COPY_GET;

		if (cur_step == M4_COPY_GET)	/* bitch if user error */
		    putchar(BELL);
		break;

	    case M4_COPY_DO_IT: 	    /* copy lines, do the copy */
		src_st = 80 * copy_p[0];    /* source start byte */
		src_end = 80 * copy_p[1] + 79;	 /* source end byte  */

		if (copy_p[2] >= copy_p[0] &&
		    copy_p[2] <= copy_p[1] )
		    {			    /* copy backwards */
		    dest_st = 80 * ( copy_p[2] + 1	/* last char to move */
				   + copy_p[1] - copy_p[0] ) -1;
		    for (i = src_end; i >= src_st; i--)
			*(scr_work + dest_st--) = *(scr_work + i);
		    }
		else
		    {			    /* copy forwards */
		    dest_st = 80 * copy_p[2];	    /* destination start byte */
		    for (i = src_st; i <= src_end; i++)
			*(scr_work + dest_st++) = *(scr_work + i);
		    }
		cur_step = M4_GET_SCREEN;   /* where we return */
		break;

	    case M4_SHOW_CURSOR:	    /* show current cursor position */
		cur_step = M4_GET_SCREEN;
		cursor_pos = TRUE;
		sprintf(med_04e[1].text, "%2d", medf_04[scr_box].col + 1);
		sprintf(med_04e[3].text, "%2d", medf_04[scr_box].line + 1);
		break;

	    case M4_DISPLAY:		    /* display the expanded screen */
		med_05(scr_work);
		cur_step = M4_GET_SCREEN;
		break;

	    case M4_SPECIAL:		    /* enter special characters */
		scr_beg();
		clrstr(0, ln_21, 80 * 3, SP3_A);       /* clear screen */
		p_msgs(med_04d, medc_04d);	    /* print instructions */
		pstr(spec_char, 0, ln_22, 160, SP3_A); /* print specials */
		putcbox(&medf_04[scr_box], &scr_work[scr_offset]); /* screen */
		scr_end();
		pcursor(col, line);
		last_char = spec_char[80 * (line - ln_22) + col];
		p = &(medf_04[scr_box]);	/* point to screen struct */
		cur_step = M4_SPECIAL_DO;
		break;

	    case M4_SPECIAL_DO:
		do
		{
		    if (col >= spec_col_max	    /* don't fall off the end */
				  && line == ln_23)
			col = spec_col_max - 1;
		    set_attr(SP3_A);
		    putchar_1(last_char);

		 /* set cursor position on main screen to reverse video */
		    pcursor(p->col,p->line);	    /* posn on main screen */
		    set_attrp(rev_vid(cur_attr[p->attr])); /* set rev attrib */
		    putchar_1(*(scr_work + 80 * p->line + p->col));

		    pcursor(col,line);
		    last_char = spec_char[80 * (line - ln_22) + col];
		    set_attr(SP4_A);
		    putchar_1(last_char);
		    pcursor(col,line);
		    ret = getraw();
/*; kludge */	    if((ret==squid_keys.home_k) || (ret==ser_keys.home_k))
			ret = 0xC7;				/*;*/
		    if((ret==squid_keys.end_k) || (ret==ser_keys.end_k))
			ret = 0xCF;
		    switch (ret)
		    {
			case 0xC7:				/*;*/
			    col = 0;
			    line = ln_22;
			    break;

			case 0xCF:
			    col = 79;
			    line = ln_23;
			    break;

			case UPARROW_KEY:
			    if (line == ln_23)
				line = ln_22;
			    break;

			case DOWNARROW_KEY:
			    if (line == ln_22)
				line = ln_23;
			    break;

			case BS_KEY:
			case LEFTARROW_KEY:
			    if (col == 0)
			    {
				if (line == ln_22)
				    break;
				line = ln_22;
				col = 79;
			    }
			    else
				col -= 1;
			    break;

			case SPACE_KEY:
			case RIGHTARROW_KEY:
			    if (col == 79)
			    {
				if (line == ln_23)
				    break;
				line = ln_23;
				col = 0;
			    }
			    else
				col += 1;
			    break;

			default:
			    break;

		    }	/* switch */

		}   /* do */
		while (ret != ENTER_KEY && ret != ESCAPE &&
		       ret != F7_KEY	&& ret != F8_KEY &&
		       ret != F9_KEY	&& ret != F10_KEY);

		if (ret == ESCAPE)
		{
		    cur_step = M4_GET_SCREEN;
		    break;
		}
		*(scr_work + 80 * p->line + p->col) = last_char; /* store */
		if (ret == ENTER_KEY)	    /* done if ENTER */
		{
		    cur_step = M4_GET_SCREEN;
		    break;
		}
		/* update screen with character */

		pcursor(p->col,p->line);	    /* posn on main screen */
		set_attr(p->attr);		    /* set rite attribute */
		putchar_1(last_char);		    /* show character on scrn */
		pcursor(col,line);		    /* posn cursor to special */

		/* adjust the cursor position on main screen */

		if (ret == F7_KEY)	    /* cursor up 1 line */
		    if (p->line > p->upper)
			p->line -= 1;

		if (ret == F8_KEY)	    /* cursor down 1 line */
		    if (p->line < p->lower)
			p->line += 1;

		if (ret == F9_KEY)	    /* cursor left 1 column */
		{
		    if (p->col == p->left)
		    {
			if (p->line != p->upper)
			{
			    p->line -= 1;
			    p->col = p->right;
			}
		    }
		    else
			p->col -= 1;
		}   /* F9_KEY */

		if (ret == F10_KEY)	    /* cursor right 1 column */
		{
		    if (p->col == p->right)
		    {
			if (p->line != p->lower)
			{
			    p->line += 1;
			    p->col = p->left;
			}
		    }
		    else
			p->col += 1;
		}   /* F10_KEY */
		break;

	    case M4_DONE:	    /* can't get here */
	    default:		    /* just in case */
		prog_err();

	}   /* switch */
    }	/*  while */

    srink(scr_work);			    /* truncate trailing blanks */
    mp->scr_len = compres(scr_work, mp->screen);    /* compress screen */
    return(SUCCESS);
}

/*** process MED screen 5 - show the screen as the user will see it *******/

med_05(scr_work)

	BYTE	*scr_work;	    /* the screen */
{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg med_05a[];
EXTERN	WORD	medc_05a;

/* Other EXTERNS */

/*  temps */

    scr_beg();
    clr_scr(cur_attr[DEF_A]);	/* clear the screen */
    display(scr_work);		/* display the screen */
    p_msgs(med_05a, medc_05a);	/* send [ANY KEY] message */
    scr_end();
    any_key();			/* wait for any key */
    return;
}

/*** process MED screen 6 - menu screen definition help *******************/

VOID	med_06()
{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_06a[];
EXTERN	WORD	medc_06a;

	BYTE	c;		    /* character temp */

    scr_beg();
    clr_scr(cur_attr[DEF_A]);
    p_msg(&title);
    p_msgs(med_06a, medc_06a);	   /* The screen */
    scr_end();
    do
	c = any_key();
    while (c != ENTER_KEY && c != F2_KEY);

    if (c == F2_KEY)
	med_07();
    return;

}   /* med_06() /*

/*** process MED screen 7 - attribute definition help *********************/

VOID	med_07()
{

EXTERN	BYTE	*cur_attr;	    /* current attribute table */

/*  Screen fields */

EXTERN	struct	scr_msg title;
EXTERN	struct	scr_msg med_07a[];
EXTERN	WORD	medc_07a;

    scr_beg();
    clr_scr(cur_attr[DEF_A]);
    p_msg(&title);
    p_msgs(med_07a, medc_07a);	   /* The screen */
    scr_end();
    any_key();
    return;

}   /* med_07() /*

/*** REV_VIDeo - change attribute to reverse video of itself ******************/

WORD	rev_vid(attr)
	WORD	attr;
{
    return( ((attr & 0x70) >> 4 ) |
	    ((attr & 0x07) << 4 ) |
	     (attr & 0x88) );
}
                                                                                                                                                                                     