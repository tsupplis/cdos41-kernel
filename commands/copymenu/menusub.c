/* MENUSUB.C - subroutines for menus					    */

/*			    Copyright (c) 1984	RTEK Inc.		    */
/*						2265 E. Becker Lane	    */
/*						Phoenix, Arizona 85028	    */
/*						(602) 867-9336		    */

/*** INCLUDE FILES **********************************************************/

#include <stdio.h>
#include <ctype.h>
#include "menu.h"

/*** DEFINES ****************************************************************/

/* definitions for expand, display, compress */

#define METACHAR 0x1b		    /* the escape character */
#define BKGATTRMASK 0x0070
#define FGNDATTRMASK 0x0007
#define BLINKBIT 0x0080
#define BRIGHTBIT 0x0008
#define IBMSTDATTR 0x0007
#define IBMREVATTR 0x0070
#define BREAKEVEN 3

#define SCREENSIZE 1920 * 2		/* size of virtual console */

#define BLACKATTR 0x0000
#define BLUEATTR 0x0001
#define GREENATTR 0x0002
#define REDATTR 0x0004
#define CYANATTR 0x0003
#define MAGENTAATTR 0x0005
#define YELLOWATTR 0x0006
#define WHITEATTR 0x0007
#define UNDERSCOREATTR 0x0001

/*** STRUCTURE DECLARATIONS ************************************************/

/*** EXTERNAL FUNCTION DECLARATIONS ****************************************/

EXTERN	LONG	lseek();
EXTERN	WORD	read();
EXTERN	WORD	write();
EXTERN	VOID	WM_MXQ();
EXTERN	VOID	wm_sync();
EXTERN	VOID	update_phys();

/*** EXTERNAL VARIABLES ****************************************************/

/*** GLOBAL VARIABLES ******************************************************/

/*** SUB FUNCTIONS *********************************************************/

/*** ReaD and verify the menu DIRectory ************************************/

WORD	rd_dir( fd , menu_dir, menu_rec )

	WORD	fd;		/* file pointer */
	BYTE	*menu_dir;	/* pointer to directory area */
	BYTE	*menu_rec;	/* record numbers of menus   */
{
	WORD	i,j;		/* temps */
	WORD	ret;		/* temp */
	LONG	lret;		/* lseek return */
	LONG	lzero = 0;	/* a long zero */

    lret = lseek( fd, lzero, 0);	/* get to start of file */
    if (lret < 0)
	return (FAILURE);

    ret = read( fd, menu_dir, DIRSIZE);  /* read in the directory */
    if ( ret < DIRSIZE )
	return (FAILURE);

    *(menu_dir + DIRSIZE) = '\0';	 /* terminate the string */

    ret = read( fd, menu_rec, WORD_SIZE * DIRCOUNT );	/* read pointers */
    if (ret < WORD_SIZE * DIRCOUNT )
	return (FAILURE);

    return(SUCCESS);
}

/*** WRite DIRectory back to the menu file ***********************************/

WORD	wr_dir( fd, menu_dir, menu_rec )
	WORD	fd;			/* menu file pointer */
	BYTE	*menu_dir;		/* pointer to directory */
	BYTE	*menu_rec;		/* menu record numbers */
{
	WORD	ret;			/* function return temp */
	LONG	lret;			/* lseek function return */
	LONG	lzero = 0;		/* a long zero */

    lret = lseek( fd, lzero, 0 );		/* point to start of file */
    if (lret < 0)
	return(FAILURE);		/* return if seek bad */

    ret = write(fd, menu_dir, DIRSIZE);
    if (ret < DIRSIZE )
	return(FAILURE);

    ret = write(fd, menu_rec, WORD_SIZE * DIRCOUNT );
    if ( ret < WORD_SIZE * DIRCOUNT )
	return(FAILURE);

    return(SUCCESS);
}

/*** ReaD MeNU from menu file *************************************************/

WORD	rd_mnu( fd, mp, menu_rec )

	WORD	fd;		    /* menu file pointer */
struct	menu	*mp;		    /* pointer to menu structure */
	WORD	menu_rec;	    /* record number of menu	*/
{
	WORD	ret;		    /* temp return variable */
	LONG	lret;		    /* lseek return */
	WORD	i;		    /* temp */

				    /* position file to start of menu */
    lret = lseek(fd, (LONG) REC_SIZE * menu_rec, 0 );
    if ( lret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->rec_len), 2 );    /* read record length */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->esc_enable), 1);  /* read escape enable flag */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->enter_enable), 1);  /* read enter enable flag */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->save_drive), 1);    /* read save drive flag */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->save_user), 1);     /* read save user flag */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->save_path), 1);     /* read save path flag */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->save_map), 1);      /* read save map flag */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->menu_spare), 16);   /* read spare space   */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, &(mp->cmd_types), 16); /* read command types */
    if ( ret < 0 )
	return (FAILURE);

    ret = read(fd, &(mp->cmd_len[0]), 32);  /* read command lengths */
    if ( ret < 0 )
	return (FAILURE);

    for ( i = 0; i < 16; i++ )
    {
						 /* read command text	 */
	if ( mp->cmd_len[i] == 0 )
	    continue;
	ret = read(fd, mp->cmd_text[i], mp->cmd_len[i] );
	if ( ret < 0 )
	    return (FAILURE);
    }

    ret = read( fd, &(mp->scr_len), 2);     /* read length of screen */
    if ( ret < 0 )
	return (FAILURE);

    ret = read( fd, mp->screen, mp->scr_len);	/* read the screen */
    if ( ret < 0 )
	return (FAILURE);

    return (SUCCESS);			    /* done, return success */
}

/*** WRite MeNU to menu file ************************************************/

WORD	wr_mnu(fd, mp )     /* returns menu record number or zero if fail */

	WORD	fd;			    /* menu file pointer */
struct	menu	*mp;			    /* menu pointer */
{
	WORD	menu_rec;		    /* record number of menu */
	WORD	ret;			    /* function return temp  */
	LONG	lret;			    /* lseek function return */
	WORD	i,j;			    /* temps */

    ret = c_wr_init();			    /* init for write operation */

    lret = lseek(fd, (LONG) 0, 2 ); /* position file to EOF */
    if ( lret < 0 )
	return (0);
    menu_rec = lret / REC_SIZE; 	      /* compute record number */
    lret = lseek(fd, (LONG) menu_rec * REC_SIZE, 0 ); /* reposn file */


			/* Compute Menu Record Length	*/
    mp->rec_len = 74;			/* length of fixed portions:	*/
					/*  2  record length		*/
					/*  6  length of flags		*/
					/* 16  length of spare space	*/
					/* 16  length of cmd types	*/
					/* 32  lengths of commands	*/
					/*  2  length of screen 	*/

    for (i = 0; i < 16; i++)		      /* determine command lengths */
    {
	mp->cmd_len[i] = srink(mp->cmd_text[i]);    /* scrink and get len */
	mp->rec_len += mp->cmd_len[i];		    /* add to record len  */
    }

    mp->scr_len = compres(mp->screen, mp->screen);  /* compress the screen */
    mp->rec_len += mp->scr_len; 		    /* add length to total */

    ret = c_write( fd, &(mp->rec_len), 2 );   /* write rec len to the file */
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->esc_enable), 1); /* write flags */
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->enter_enable), 1);
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->save_drive), 1);
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->save_user), 1);
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->save_path), 1);
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->save_map), 1);
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->menu_spare), 16);
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->cmd_types[0]), 16 ); /* write command types */
    if ( ret < 0 )
	return (0);

    ret = c_write( fd, &(mp->cmd_len[0]), 32);	/* write command lengths */
    if ( ret < 0 )
	return (0);

    for (i = 0; i < 16; i++)			    /* write commands */
    {
	ret = c_write( fd, mp->cmd_text[i], mp->cmd_len[i] );
	if ( ret < 0 )
	    return (0);
    }
    ret = c_write( fd, &(mp->scr_len), 2 );	      /* write screen length */
    if ( ret < 0 )
	return (0);

/*	Some hacking going on here - The 'C' i/o system doesn't seem to */
/*	work if you do a 128 byte write when the file is positioned on	*/
/*	a 128 byte boundry.  So, we write 1 extra byte if the total length */
/*	of the menu is = 0 mod 128					*/

    i = mp->scr_len;
    if ( mp->rec_len % 128 == 0)
	i += 1;

    ret = c_write( fd, mp->screen, mp->scr_len);	 /* write screen */
    if ( ret < 0 )
	return (0);

/*  pad to full record length with junk */
/*  ret = REC_SIZE - (mp->rec_len % REC_SIZE );  */
/*  if (ret != REC_SIZE)	  */

/*  write( fd, mp->screen, 128 );		    /* so it works */

/*  lret = lseek(fd, (LONG) REC_SIZE * menu_rec, 0);	/* reposn file */
/*  ret = write( fd, &(mp->rec_len), 2 );   /* write rec len to the file */
/*  if ( ret < 0 )
/*	return (0);			    */

    ret = c_wr_buf(fd); 		   /* truncate last buffer */

    return (menu_rec);				/* return menu record number */
}

/*  Some subroutines to block all write i/o to 128 byte blocks */

GLOBAL	WORD	cur_count;
GLOBAL	BYTE	t_buf[129];

WORD	c_wr_init()
{
    cur_count = 0;
    return (0);
}

WORD	c_write(fd, buf, count)

	WORD	fd;
	BYTE	*buf;
	WORD	count;
{
	WORD	i;
	WORD	ret;

    for (i = 0; i < count; i++)
    {
       if (cur_count == 128)
	    ret = c_wr_buf(fd);
	t_buf[cur_count++] = *(buf + i);
    }
    return (count);
}

WORD	c_wr_buf(fd)

	WORD	fd;
{
	WORD	ret;

    if (cur_count > 0)
	ret = write(fd, &t_buf[0], 128);
    else
	ret = 1;
    cur_count = 0;
    return(ret);
}

/*** ScRINK a string (truncate trailing blanks) ******************************/

WORD	srink(ptr)

	BYTE	*ptr;

{
	BYTE	*ptr0,*ptr1;		    /* temp string pointers */
	ptr0 = ptr;			    /* remember start of string */
	ptr1 = ptr - 1; 		    /* set so null string is null */
	while (*ptr != '\0')		    /* look for non blank till end */
	{
	    if ( *ptr != ' ')		    /* remember last non-blank */
		ptr1 = ptr;
	    ptr += 1;
	}
	*(++ptr1) = '\0';		    /* store new string terminator */
	return (ptr1 - ptr0 + 1);	    /* return string length incl 0 */
}

/*** COMPRESs the menu screen ************************************************/

WORD	compres( srce, dest )	       /* returns length of output string */

	BYTE	*srce;			    /* pointer to expanded screen */
	BYTE	*dest;			    /* pointer to compressed screen */
{
	WORD	i;			    /* temp */
	BOOLEAN not_done;		    /* while controller */
	BYTE	*outstr;		    /* temp output pointer */
	BYTE	prev_char = 0xff;	    /* previous char for repeat cnt */
	WORD	rpt_count = 0;		    /* number of prev_chars in a row */

    outstr = dest;
    not_done = TRUE;

    while ( not_done )
    {
	if ( prev_char == *srce && rpt_count < 255 )
	    rpt_count += 1;
	else
	{
	    if ( rpt_count > BREAKEVEN )
	    {
		*(outstr++) = METACHAR;
		*(outstr++) = (BYTE) rpt_count;
		*(outstr++) = prev_char;
	    }
	    else
		for (i = 0; i < rpt_count; i++)
		    *(outstr++) = prev_char;
	    rpt_count = 1;
	    prev_char = *srce;
	}   /* else */

	if (prev_char == '\0')
	    not_done = FALSE;

	srce += 1;

    }	/* while */

    *(outstr++) = '\0'; 		/* mark end of output string */
    return (outstr - dest);		/* return length incl 0 to caller */
}

/*** EXPAND the menu screen ************************************************/

WORD	expand( srce, dest )		   /* returns length of output string */

	BYTE	*srce;			    /* pointer to compressed screen */
	BYTE	*dest;			    /* pointer to return string */
{
	WORD	i;			    /* temp */
	BYTE	*outstr;		    /* temp output pointer */
	WORD	rpt_count;		    /* number of prev chars in a row */
	BYTE	c;			    /* temp character */

    outstr = dest;

    while ( *srce )
    {
	if (*srce == METACHAR)
	{
	    rpt_count = *(++srce);
	    c = *(++srce);
	    while (rpt_count-- > 0)
		*(outstr++) = c;
	}
	else
	    *(outstr++) = *srce;
	srce += 1;
    }	/* while */

    srce = dest + SCREEN_SIZE;		/* where to store \0  */
    while (outstr < srce)
	{
	*outstr++ = ' ';		/* blank out the rest */
	i -= 1;
	}
    *outstr = '\0';			/* mark end of output screen */
    return (SCREEN_SIZE);		/* return length to caller */
}

/*** DISPLAY the menu screen ************************************************/

WORD	display( ptr )			    /* returns attribute character */

	BYTE	*ptr;			    /* pointer to compressed screen */
{
EXTERN	WORD	vc_segment;		    /* seg addr of our virt screen */
EXTERN	BOOLEAN is_mono;		    /* true if monochrome monitor */
	WORD	i;			    /* temp */
	WORD	offset = 0;		    /* current screen offset */
	WORD	attr = IBMSTDATTR;	    /* current attribute */
	WORD	blank_count = 0;	    /* number of buffered blanks */
	BOOLEAN rev_video = FALSE;	    /* reverse video mode */
	BOOLEAN under_score = FALSE;	    /* underscore mode switch */
	BOOLEAN not_done = TRUE;	    /* while controller */

    while ( not_done )
    {
	switch ( *ptr )
	{
	case '\\':			  /* toggle reverse video */
	    attr = (attr & ~(BKGATTRMASK | FGNDATTRMASK) )
			 | ((attr & BKGATTRMASK) >> 4)
			 | ((attr & FGNDATTRMASK) << 4);
	    blank_count += 1;		    /* increment buffered blanks */
	    break;

	case '_':			  /* toggle underscore */
	    blank_count += 1;		    /* increment buffered blanks */
	    if (is_mono == FALSE)
		break;
	    if (under_score)
	    {
		attr = attr & ~(BKGATTRMASK | FGNDATTRMASK) ;
		attr = attr | IBMSTDATTR;	   /* if on, set off */
		under_score = FALSE;
	    }
	    else
	    {
		attr = attr & ~(BKGATTRMASK | FGNDATTRMASK) ;
		attr = attr | UNDERSCOREATTR;	   /* if off, set on */
		under_score = TRUE;
	    }
	    break;

	case '}':			  /* toggle bright */
	    attr = attr ^ BRIGHTBIT;	    /* set/reset the attribute bit */
	    blank_count += 1;		    /* incr buffered blanks */
	    break;

	case '{':			  /* toggle blink */
	    attr = attr ^ BLINKBIT;	    /* set/reset blink bit */
	    blank_count += 1;		    /* incr number of buffered blanks */
	    break;

	case '|':			  /* set background color */
	    ptr += 1;			    /* get to new attr char */
	    blank_count += 2;		    /* incr number of buffered blks */
	    if (is_mono)
		break;
	    if (isupper(*ptr))
		if ( blank_count > 0 )
		{
						/* output buffered blanks */
		    FREPEAT(' ', offset, blank_count, attr, vc_segment );
		    offset += ( blank_count << 1 );	/* incr screen offset */
		    blank_count = 0;			/* reset counter */
		}
	    attr = attr & ~BKGATTRMASK;     /* clear background attr */
					    /* set new bkg attr */
	    attr = attr | ( get_attr(*ptr,attr) << 4 );
	    break;

	case '~':			  /* set foreground color */
	    ptr += 1;			    /* get to new attr char */
	    blank_count += 2;		    /* inc number of buffered blnks */
	    if (is_mono)
		break;
	    attr = attr & ~FGNDATTRMASK;    /* clear foreground attr */
	    attr = attr | ( get_attr(*ptr,attr));/* set new fgnd attr */
	    break;

	case METACHAR:			  /* repeated character */
	    if ( blank_count > 0 )
	    {
					    /* output buffered blanks */
		FREPEAT(' ', offset, blank_count, attr, vc_segment );

		offset += ( blank_count << 1 );     /* incr screen offset */
		blank_count = 0;		    /* reset counter */
	    }
	    ptr += 1;			    /* get to character count */
	    i = *ptr;			    /* get count to word */
	    ptr += 1;			    /* get to character */
	    FREPEAT(*ptr, offset, i, attr, vc_segment ); /* put them out */
	    offset += ( i  << 1 );	    /* incr screen offset */


/*  This is the slow way, should just keep tract of the number */
/*  of regular characters, then when a non-regular is found, do */
/*  just one call to FDRAW */

	default:			    /* regular characters */
	    if ( blank_count > 0 )
	    {
					    /* output buffered blanks */
		FREPEAT(' ', offset, blank_count, attr, vc_segment );

		offset += ( blank_count << 1 );     /* incr screen offset */
		blank_count = 0;		    /* reset counter */
	    }

	    if ( *ptr == '\0' )
	    {
		not_done = FALSE;
		break;
	    }

	    FREPEAT(*ptr, offset, 1, attr, vc_segment ); /* output the char */
	    offset += 2;		    /* increment screen offset */
	    break;
	}   /* switch */

	ptr += 1;

    }	/* while */

/*  if ( offset <= SCREENSIZE ) 	    /* clear the rest of the scrn */
/*   FREPEAT (' ', offset, (SCREENSIZE - offset + 2 ) / 2, attr, vc_segment);*/
    return (attr);			    /* return attr to caller */
}

/*** GET ATTRibute from letter on screen **************************************/

WORD	get_attr(ch,attr)
	BYTE	ch;
	WORD	attr;			/* return if error */
{
    switch(ch)
    {
    case 'k':				  /* black */
    case 'K':				  /* black */
	return (BLACKATTR);

    case 'b':				  /* blue  */
    case 'B':				  /* blue  */
	return (BLUEATTR);

    case 'g':				  /* green */
    case 'G':				  /* green */
	return (GREENATTR);

    case 'r':				  /* red   */
    case 'R':				  /* red   */
	return (REDATTR);

    case 'c':				  /* cyan  */
    case 'C':				  /* cyan  */
	return (CYANATTR);

    case 'm':				  /* magenta */
    case 'M':				  /* magenta */
	return (MAGENTAATTR);

    case 'y':				  /* yellow */
    case 'Y':				  /* yellow */
	return (YELLOWATTR);

    case 'w':				  /* white */
    case 'W':				  /* white */
	return (WHITEATTR);

    default:
	return(attr);
	break;
    break;
    }	/* switch */
}

/*** FiND MeNU name in directory, return index (0 relative, -1 if none ) *****/

WORD	fnd_mnu( menu_dir, menu_name )

	BYTE	*menu_dir;		/* menu directory */
	BYTE	*menu_name;		/* zero terminated menu name */
{
	BYTE	menu_temp[8];		/* blank filled version */
	WORD	i,j,k;			/* temps */

    for (i = 0; i < 8; i++)
	menu_temp[i] = ' ';

    i = 0;
    while (*menu_name)			/* move chars to temp location */
	menu_temp[i++] = *(menu_name++);
    for ( i = 0; i < DIRSIZE; i += 8 )
    {
	k = 0;
	j = i;
	while ( menu_dir[j++] == menu_temp[k] && k++ < 8 )
	;				/* null statement */
	if ( k == 8 )
	    return( i / 8 );		/* return the index */
    }
    return ( -1 );			/* fail */
}

/*** DELete MeNU - delete a menu from the directory ***************************/

VOID	del_mnu( menu_dir, menu_num )
	BYTE	*menu_dir;		    /* the menu directory */
	WORD	menu_num;		    /* the zero relative index */
{
	WORD	i,j;			    /* temps */

    i = menu_num * DIRNAMELEN;		/* starting index of dir entry */
    for (j = 0; j < DIRNAMELEN; j++)
	menu_dir[i++] = ' ';
    return;
}

/*** UPDate DIR - store new menu name in directory ***************************/

VOID	upd_dir( menu_dir, menu_num, menu_name )
	BYTE	*menu_dir;		    /* the menu directory */
	WORD	menu_num;		    /* the zero relative index */
	BYTE	*menu_name;		    /* the new menu name  */
{
	WORD	i,j;			    /* temps */

    i = menu_num * DIRNAMELEN;		/* starting index of dir entry */
    for (j = 0; j < DIRNAMELEN; j++)
    {
	if ( *menu_name != '\0' )
	    menu_dir[i++] = *(menu_name++);
	else
	    menu_dir[i++] = ' ';
    }
    return;
}

/*** CLeaR MeNU (setup for new menu) ****************************************/

VOID	clr_mnu(mp)
struct	menu	*mp;			    /* the menu */
{
	WORD	i,j;			    /* temps */

    mp->rec_len = 0;
    mp->esc_enable = 'N';
    mp->enter_enable = 'N';
    mp->save_drive = 'N';
    mp->save_user = 'N';
    mp->save_path = 'N';
    mp->save_map = 'N';
    for (i = 0; i < 16; i++)		    /* command types & text */
    {
	mp->cmd_types[i] = ' ';
	for (j = 0; j < 128; j++)
	    *(mp->cmd_text[i] + j) = ' ';
	*(mp->cmd_text[i] + 128) = '\0';
    }
    for (i = 0; i < 1920; i++)		    /* screen */
	*(mp->screen + i) = ' ';
    *(mp->screen + 1920) = '\0';

    return;
}
                                                                                                                                                                                                   