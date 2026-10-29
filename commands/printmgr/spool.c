/************************************************************************
*									*
*	CONCURRENT CP/M-86 SPOOLER INTERFACE UTILITY 			*
*									*
*************************************************************************

	SPOOL gives the user a method of using the spooler rsp's by
	opening and managing the spooler control queues. SPOOL can do
	the following:
	o	spool one or more files
	o	spool multiple copies of any file
	o	abort spooler jobs
	o	get spooler status
	o	change the spooler's default user and drive
	o	temporarily disable the spooler
	o	re-enable the spooler

**************************************************************************

	Created:	4 October 1983
	by:		Kevin Schoch

	History:
	11/10/83	New version started for full functionality
	11/19/83	Basic functionallity in place and working
	11/20/83	abort processing
	12/05/83	option processing
	01/05/84	termination processing
	01/11/84	copies processing
*************************************************************************
	01/24/84	New program with new format
	01/26/84	Functional
	01/28/84	Tab expansion ok
	01/31/84	Help option ok
	01/31/84	option parsing in do_print is ok
	02/01/84	page breaks and fomatting ok
	02/02/84	magins, nofeed and command line startup

*************************************************************************/
/*
	**************************
	*   COPYRIGHT (C) 1984   *
	*  DIGITAL RESEARCH INC. *
	*  P.O. BOX 579		 *
	*  PACIFIC GROVE, CA   	 *
	*	 93950 	 	 *
	**************************
*/


#include	"stdio.h"



#include	"cpmcall.h"



#include	"ctype.h"



#include	"spldef.h"



					/* TOKEN DEFINE LIST	*/

#define		T_PRINT		01	/* this is the default verb */
#define		T_COPIES	02
#define		T_STATUS	03
#define		T_START		04
#define		T_DELETE	05
#define		T_HELP		06
#define		T_TERMINATE	07
#define		T_ALL		08
#define		T_QMARK		*token[09]	/* ? */
#define		T_EQUAL		*token[10]	/* = */
#define		T_LBRACKET	*token[11]	/* [ */
#define		T_RBRACKET	*token[12]	/* ] */
#define		T_TAB		*token[13]
#define		T_EOF		a_eof		/* hex 1A */
#define		T_COMMA		*token[14]
#define		T_SPACE		*token[15]
#define		T_TABS		16
#define		T_FORM		17
#define		T_PAGE		18
#define		T_FORMAT	19
#define		T_NOFEED	20
#define		T_MARGIN	21
#define		T_NUMBER	22
#define		T_PRINTER	23
#define		T_RESET		24
#define		T_FF		a_ff
#define		T_LF		a_lf
#define		T_CR		a_cr

#define		READ_SIZE	1024	/* read buffer size*/
#define		D_SIZE		128	/* spooler transaction buf size	*/



/*-------------------------------------
	EXTERNALS
-------------------------------------*/

EXTERN	UBYTE  *token[];		/* command syntax tokens	*/
EXTERN	UBYTE  *message[];		/* user messages (general)*/
EXTERN	UBYTE  *error[];		/* error messages	*/


/****************************************
* DYNAMIC LOADING FOR DESPOOLERS  	*
****************************************/

EXTERN	UBYTE cli_dsp[];		/* send CLI buffer	*/
EXTERN	UBYTE cli_spl[];		/* send CLI buffer	*/

EXTERN	UBYTE *splmsg[];		/* user messages	*/

UBYTE	*copyright = "COPYRIGHT (C) 1984 DIGITAL RESEARCH XXXX-0000-654321";

struct s_spl	splbuf;			/* spooler message buffer	*/
struct s_spl	initbuf =		/* used for initiating jobs	*/
{
    0,0,
    0,0,0,0,0,0,0,0,0,0,0,
    0,0,0x80,1,1,0,0,0
};


struct xdos_qpb	mxspl =			/* mxspl qpb		*/
{
    0,0,0,0,0,
    'M','X','S','P','L',' ',' ',' '
};

struct xdos_qpb	splin =			/* splin qpb		*/
{
    0,0,0,0,&splbuf,
    'S','P','L','I','N',' ',' ',' '
};

struct xdos_qpb	splout =		/* splout qpb		*/
{
    0,0,0,0,&splbuf,
    'S','P','L','O','U','T',' ',' '
};


EXTERN	UBYTE	a_eof, a_ff, a_lf, a_cr;


/*******************
* Global Variables *
*******************/
UWORD	g_tabs = 8;			/* spaces to expand tabs to	*/
UWORD	g_chars = 0;			/* char position on line	*/
UWORD	g_lines = 0;			/* current line count	*/
UWORD	g_pages	= 1;			/* pages		*/
UWORD	g_form_size = 66;		/* form size		*/
UWORD	g_page_size = 66;		/* page size		*/
UWORD	g_pformat = FALSE;		/* format page flag	*/
UWORD	g_nofeed = FALSE;		/* do form feed before job	*/
UWORD	g_number = FALSE;		/* number pages		*/
UWORD	g_margin = 8;			/* left margin count	*/
UWORD	g_printer = 0;			/* default printer number	*/





main(argc, argv)
UBYTE	argc;
UBYTE	*argv[];
/****************************************************************/
/*								*/
/*			MAIN ROUTINE				*/
/*								*/
/****************************************************************/
{

/*-------------------------------------
	INITIALIZATION
-------------------------------------*/

    XDOS(C_MODE, 0x09);			/* ^C off, status on	*/
    XDOS(F_ERRMODE, 0xFF);			/* set return error mode*/


/*-------------------------------------
	COMMAND LINE PROCESSING
-------------------------------------*/

    if (argc>1)	
	cmd_proc(argc, argv);		/* process command line	*/
    else
	puts(message[01]);		/* usage message	*/


    exit(SUCCESS);
}




cmd_proc(ac, av)
UWORD	ac;				/* command argument count	*/
UBYTE	**av;				/* command argument pointers	*/
/****************************************************************/
/*								*/
/*			COMMAND LINE PARSER			*/
/*								*/
/****************************************************************/
{
    REG UWORD	i;
    REG UBYTE	*s;
    UBYTE	*t;

    i=0;
    t=av[ac];				/* end of arguments pointer	*/

    while((s=av[++i]) != t)		/* while arguments	*/
	while(*s = toupper(*s))		/* convert to upper case	*/
	    ++s;			/* next character	*/

    if ((i=get_token(*(++av))) == 0) {	/* check for token	*/
	i=T_PRINT;			/* default to print verb	*/
	--ac;				/* adjust arg list for no verb	*/
    }
    else {
	++av;
	--ac;
	--ac;
    }

    return (opt_select(i, ac, av));	/* go do the action	*/
}



/*------------------------------------------------------------------------
	SPOOL UTILITY FUNCTION PROCESSING
------------------------------------------------------------------------*/

do_print(pc, pv)
UWORD	pc;
UBYTE	**pv;
/****************************************************************/
/*								*/
/*		PRINT FILES FROM COMMAND LINE			*/
/*								*/
/****************************************************************/
{
    REG UBYTE *s;
    REG UWORD i;
    WORD t;
    UBYTE read_buf[READ_SIZE];		/* input buffer	*/
    WORD fd, c_count;			/* file descriptor	*/
    UWORD copies;			/* number of copies	*/
    UWORD jobid, j;			/* current job number	*/
    struct bdos_fcb tfcb;		/* temp. file cntl block*/
    struct s_pfcb {			/* parse fcb for fn 152	*/
	UBYTE	*filspec;
	UBYTE	*fcbspec;
    } pfcb;
    UBYTE exp_buf[128];			/* char expansion buf	*/
    UWORD exp_cnt, e;			/* expansion count	*/
    UWORD tl, bl, pl;			/* top l, bot. l, page l*/

    UBYTE opt_buf[40], *opt, *oarg, *next_opt;
					/* option parsing ptr.s	*/


    opt_buf[0]=NULL;
    g_printer=XDOS(L_GET);
    copies=1;
    i=pc;
    while (i--) {
	if (*pv[i]==T_LBRACKET)	{
	    e=pc;
	    pc=i;			/* set new arg count	*/
	    while (i<e)
		strcat(opt_buf, pv[i++]);
	    next_opt=&opt_buf[1];
	    while (next_opt) {		/* while options left	*/
		opt=next_opt;
		next_opt=NULL;
		i=0;
		while (opt[i]) {
		    if (opt[i]==T_EQUAL) {
			oarg=&opt[i+1];
			opt[i]=NULL;
		    }
		    if (opt[i]==T_COMMA) {
			next_opt=&opt[i+1];
			opt[i]=NULL;
			break;
		    }
		    if (opt[i]==T_RBRACKET) {
			opt[i]=NULL;
			next_opt=NULL;
			break;
		    }
		    ++i;
		    if (i>40) {
			puts(error[05]);
			return FAILURE;
		    }
		}

		switch (get_token(opt)) {
		case T_PRINT:		/* the tokens are so close*/
		case T_PRINTER:
		    g_printer=atoi(oarg);
		    printf(message[02], g_printer);
		    break;

		case T_COPIES:
		    copies=atoi(oarg);
		    if (copies > 254)
			copies=254;
		    printf(message[19], copies);
		    break;

		case T_TABS:
		    g_tabs=MAX(MIN(atoi(oarg), 30), 0);
		    printf(message[20], g_tabs);
		    break;

		case T_FORM:
		    g_form_size=atoi(oarg);
		    g_pformat=TRUE;
		    printf(message[21], g_form_size);
		    break;

		case T_PAGE:
		    g_pformat=TRUE;
		    g_page_size=atoi(oarg);
		    printf(message[22], g_page_size);
		    break;

		case T_FORMAT:
		    g_pformat=TRUE;
		    break;

		case T_NOFEED:
		    g_nofeed=TRUE;
		    puts(message[24]);
		    break;

		case T_MARGIN:
		    g_margin=MAX(MIN(atoi(oarg), 50), 0);
		    printf(message[25], g_margin);
		    break;

		case T_NUMBER:
		    g_number=TRUE;
		    g_pformat=TRUE;
		    puts(message[26]);
		    break;

		default:
		    puts(error[05]);	/* unknown opt */
		    return(FAILURE);
		}
	    }

	    if (g_pformat==TRUE)
		puts(message[23]);

	    if (g_form_size <= g_page_size+1) {
		puts(error[08]);
		return FAILURE;
	    }

	    if ((g_form_size-g_page_size) > 100) {
		puts(error[07]);
		return FAILURE;
	    }

	    i=0;
	}
    }

    initbuf.lst_spl=g_printer;		/* set lst: number	*/
    initbuf.cpy_spl=copies;		/* set copy count	*/
    initbuf.clp_spl=copies;

    for (i=0; i<pc; i++) {

	if ((fd=openb(pv[i], 0)) == FAILURE) {
					/* open first file RO	*/
	    printf(error[04], pv[i]);	/* could not open	*/
	    continue;
	}

	g_lines=0;
	g_chars=0;
	g_pages=1;
	tl=(g_form_size-g_page_size)/2;	/* top printed line	*/
	bl=tl+g_page_size;		/* bottom line	*/
	pl=bl+(tl/2);			/* page number line	*/

	pfcb.fcbspec=&tfcb;
	pfcb.filspec=pv[i];
	j=0;

	while (pv[i][j])		/* check for 2a:*.* stuff*/

	    if (pv[i][j++] == ':') {	/* only the *.* should be*/
					/* be in the job name	 */
		pfcb.filspec=&pv[i][j];
		break;
	    }

	XDOS(F_PARSE, &pfcb);		/* parse file name	*/

	for (j=0; j<8; j++)		/* copy file name	*/
	    initbuf.nam_spl[j]=tfcb.fn[j];

	for (j=0; j<3; j++)
	    initbuf.nam_spl[j+8]=tfcb.ft[j];

	splin.bfptr_qp=&initbuf;	/* get a job started	*/

	XDOS(Q_READ, &mxspl);		/* get the mx	*/
	XDOS(Q_WRITE, &splin);		/* write job initiate	*/

	splin.bfptr_qp=&splbuf;
	XDOS(Q_READ, &splout);		/* get the result	*/
	XDOS(Q_WRITE, &mxspl);		/* put the mx back	*/

	jobid=splbuf.job_spl;		/* record job id	*/

	puts("");
	printf(message[08], jobid);	/* print job id, name	*/
	printf("%s%s ... ", message[05], pv[i]);


	switch(splbuf.cmd_spl) {	/* check error cond.*/

	case 00:
	    break;			/* success	*/

	case 01:
	    puts(message[06]);		/* unsuccessful	*/
	    puts(error[14]);		/* invalid lst:	*/
	    continue;

	case 02:
	    puts(message[06]);		/* unsuccessful	*/
	    puts(error[15]);		/* file system error	*/
	    continue;

	case 03:
	    puts(message[06]);		/* unsuccessful	*/
	    puts(error[16]);		/* over spooling limit	*/
	    return FAILURE;

	case 04:
	    puts(message[06]);		/* unsuccessful	*/
	    puts(error[17]);		/* job limit exceeded	*/
	    return FAILURE;

	default:
	    puts(message[06]);		/* unsuccessful	*/
	    puts(error[10]);		/* impossible error	*/
	    return FAILURE;
	}

	while (c_count=read(fd, read_buf, READ_SIZE)) {
	    if (c_count == FAILURE) {
		puts(message[06]);	/* failure	*/
		puts(error[13]);	/* file system error	*/
		break;
	    }

	    if ((UBYTE)XDOS(C_STAT) == 0x01) {
		XDOS(C_RAWIO, 0xFD);		/* pull out the ^C	*/
		puts(message[06]);	/* unsuccessful	*/
		close(fd);
		splbuf.cmd_spl=2;	/* send an abort	*/
		splbuf.job_spl=jobid;
		send_packet();
		return FAILURE;
	    }

	    j=0;			/* j send buffer pointer*/

	    for(t=0; t<c_count; t++) {
		j=p_format(tl, bl, pl, j, jobid);
					/* format page */
		exp_cnt=expand(read_buf[t], exp_buf);

		if (j+exp_cnt > D_SIZE) {
		    send_buf(jobid);	/* send j chars	*/
		    j=0;		/* send buffer is clear	*/
		}

		for (e=0; e<exp_cnt; e++) {
		    if (exp_buf[e] == T_EOF) {
			exp_cnt=0xFF;
			break;
		    }

		    splbuf.dat_spl[j++]=exp_buf[e];
		    splbuf.byt_spl=j;
		}

		if (exp_cnt==0xFF)
		    break;		/* end of file escape	*/
	    }

	    send_buf(jobid);		/* flush the send buffer*/
	    j=0;

	    if (exp_cnt==0xFF) {
		c_count=0;
		break;
	    }

	}

	if (g_pformat && g_number) {	/* if formating enabled then do this on*/
	  				/* the last page		*/
	    while (++g_lines < pl) {

		if (j ==128) {
		    send_buf(jobid);
		    j=0;
		}

		splbuf.dat_spl[j++]=T_CR;
		splbuf.dat_spl[j++]=T_LF;
		splbuf.byt_spl = j;
	    }

	    send_buf(jobid);

	    j=0;
	    for (e=0; e<40; e++)	/* spaces to number	*/
		splbuf.dat_spl[j++]=T_SPACE;

	    sprintf(&splbuf.dat_spl[j], "%4d", g_pages);
					/* page number	*/
	    j += 4;
	    splbuf.byt_spl=j;
	    send_buf(jobid);		/* clear buffer	*/
	    j=0;

	} /* end of last page formating 		 */


	if (c_count == SUCCESS)		/* end of file reached	*/
	    puts(message[07]);

	close(fd);
	splbuf.cmd_spl=0x07;		/* terminate the job	*/
	splbuf.job_spl=jobid;
	send_packet();			/* send to spooler	*/
    }

    return(SUCCESS);

}




p_format(tl, bl, pl, j, jobid)
UWORD  tl;
UWORD bl;
UWORD pl;
UWORD j;
UWORD jobid;
/****************************************************************/
/*								*/
/*			Page Formatting				*/
/*								*/
/****************************************************************/
{
    UWORD a, b, c;


    if (g_nofeed==FALSE && g_chars==0 && g_lines==0 && g_pages==1) {
					/* insert form feed	*/
	if (g_pformat==FALSE)
	    ++g_pages;
	splbuf.dat_spl[j++]=T_FF;
	splbuf.dat_spl[j++]=T_CR;
	splbuf.byt_spl=j;
	send_buf(jobid);
	j=0;
    }

    if (g_pformat==FALSE)		/* check format flag	*/
	return j;

    if (g_lines == bl) {		/* bottom of page found	*/
	send_buf(jobid);
	j=0;
	while (g_lines++ <= pl) {	/* lines to page number	*/
	    splbuf.dat_spl[j++]=T_CR;
	    splbuf.dat_spl[j++]=T_LF;
	}

	if (g_number) {
	    for (a=0; a<36; a++)	/* spaces to number	*/
		splbuf.dat_spl[j++]=T_SPACE;

	    sprintf(&splbuf.dat_spl[j], "%4d", g_pages);
					/* page number */
	    g_pages++;
	    j += 4;
	}

	--g_lines;
	while (g_lines++ < g_form_size) {
					/* lines to end-of-page	*/
	    splbuf.dat_spl[j++]=T_CR;
	    splbuf.dat_spl[j++]=T_LF;
	}

	splbuf.byt_spl=j;
	send_buf(jobid);		/* clear buffer	*/
	j=0;
	g_lines=0;
	g_chars=0;			/* set char position	*/
    }

    if (g_lines == 0) {			/* top of the page	*/
	while (g_lines++ < tl) {	/* lines to top of page	*/
	    splbuf.dat_spl[j++]=T_CR;
	    splbuf.dat_spl[j++]=T_LF;
	}

	--g_lines;
	splbuf.byt_spl=j;
	send_buf(jobid);
	j=0;
	g_chars=0;
    }

    return(j);
}





expand(c, ebuf)
UBYTE	c;				/* character to expand	*/
UBYTE	*ebuf;				/* expansion buffer	*/
/****************************************************************/
/*								*/
/*			Expand a Character			*/
/*								*/
/****************************************************************/
{
    UWORD	rc;
    UWORD	a, cc;
    UWORD	save;


    rc=0;

    if (g_chars == 0)
	for (a=0; a<g_margin; a++)

    ebuf[rc++]=T_SPACE;

    if (c == T_TAB) {
	save=g_tabs-(g_chars % g_tabs);
	for (cc=0; cc<save; cc++)
	    ebuf[cc+rc]=T_SPACE;
	g_chars += save;
	rc += cc;
    }
    else if (c == T_EOF)
	ebuf[rc++]=T_EOF;
    else {
	++g_chars;
	ebuf[rc++]=c;
    }

    if (c == T_LF) {			/* on line feed	*/
	g_chars=0;			/* char position = 0	*/
	g_lines = (g_lines+1) % g_form_size;	/* new line number	*/
    }

    return(rc);
}




send_buf(jobnum)
UBYTE	jobnum;
/****************************************************************/
/*								*/
/*			Send a Buffer to Spooler		*/
/*								*/
/****************************************************************/
{
    UWORD e;


    splbuf.cmd_spl=0x01;
    splbuf.job_spl=jobnum;

    if (XDOS(Q_WRITE, &splin)) {		/* do a spooler trasaction*/
	puts(message[06]);
	exit FAILURE;
    }
    return(SUCCESS);
}



EXTERN	UBYTE *helps[];			/* help messages	*/

do_help()
/****************************************************************/
/*								*/
/*		SEND HELP TO THE USER				*/
/*								*/
/****************************************************************/
{
    REG UBYTE **hline;


    hline=helps;
    while (**(++hline) != **helps)
	if (**hline == *(*helps+1)) {
	    puts(message[04]);		/* type any key to continue	*/
	    XDOS(C_RAWIO, 0xFD);
	}
	else
	    puts(*hline);

    return(SUCCESS);
}




do_start(dspcount, dsps)
UWORD	dspcount;
UBYTE	**dsps;
/****************************************************************/
/*								*/
/*		STARTUP THE SPOOLER PROCESS			*/
/*								*/
/****************************************************************/
{
    UBYTE	c;
    UWORD	dspflg;			/* despooler set flag	*/
    UWORD	d;


    dspflg=FALSE;

    if (!XDOS(Q_OPEN,&mxspl) || !XDOS(Q_OPEN,&splin) || !XDOS(Q_OPEN,&splout)) {
	puts(error[06]);		/* already set up */
	return FAILURE;
    }

    if (check_net()) {			/* is network ok */
	puts(splmsg[03]);
	puts(splmsg[04]);
	puts(splmsg[07]);
	exit(FAILURE);
    }

    XDOS(P_PRIORITY, 50);			/* boost your priority	*/

    puts(splmsg[01]);

    for (c=0; c<2; c++)			/* print banner	*/
	puts(splmsg[c]);

    c=0;
    while (c++ < dspcount) {
	d=atoi(*(dsps++));		/* dsp/printer number	*/
	printf(splmsg[02], d);

	if (d<0 || d>15) {
	    puts(message[06]);
	    puts(splmsg[06]);		/* out of range message	*/
	    continue;
	}

	if (XDOS(L_SET, d)) {		/* set list device	*/
	    puts(message[06]);
	    puts(splmsg[05]);		/* number not supported	*/
	    continue;
	}

	if (XDOS(P_CLI, cli_dsp)!=NULL) {	/* start despooler	*/
	    XDOS(C_ATTACH);
	    puts(message[06]);
	    puts(splmsg[10]);		/* no dsp.cmd or lstnn:*/
	    puts(splmsg[11]);
	    continue;
	}

	dspflg=TRUE;
	XDOS(C_ATTACH);			/* grab the console	*/

/* the despooler will write success on the console	*/
    }

    if (dspflg != TRUE) {
	puts("");
	puts(splmsg[08]);		/* no despoolers setup	*/
	puts(splmsg[09]);
	return FAILURE;
    }

    XDOS(F_DMAOFF, cli_spl);			/* set dma address to	*/
    XDOS(P_CHAIN);				/* start the spooler	*/
    XDOS(C_ATTACH);				/* grab the console	*/
    XDOS(P_PRIORITY, 200);			/* restore priority	*/
    return(SUCCESS);
}




do_delete(ccmd, cmd)			/* abort a spooler job	*/
UWORD ccmd;
UBYTE **cmd;				/* argv		*/
/****************************************************************/
/*								*/
/*			DELETE A JOB				*/
/*								*/
/****************************************************************/
{


    if (get_token(cmd[0]) == T_ALL) {
	puts("The ALL jobs option not available.");
	return FAILURE;
    }

    if (!isdigit(*cmd[0])) {
	puts(error[03]);		/* not a number	*/
	return FAILURE;
    }

    splbuf.cmd_spl=2;			/* spooler abort command*/
    splbuf.job_spl=atoi(cmd[0]);	/* job number	*/
    printf(message[11], splbuf.job_spl);

    if (send_packet()) {
	puts(message[06]);		/* unsuccessful	*/
	puts(error[20]);		/* invalid job id	*/
	return FAILURE;
    }

    puts(message[07]);
    return SUCCESS;
}




do_reset()
/****************************************************************/
/*								*/
/*			DO_RESET				*/
/*								*/
/****************************************************************/
{


    puts(message[03]);
    XDOS(Q_READ, &mxspl);
    splbuf.cmd_spl=0x0A;		/* terminate the spooler	*/
    splbuf.job_spl=0x01;		/* don't save any jobs	*/
    XDOS(Q_WRITE, &splin);

    return SUCCESS;
}




do_terminate()				/* terminate spooler system	*/
/****************************************************************/
/*								*/
/*			DO_TERMINATE				*/
/*								*/
/****************************************************************/
{


    puts(message[09]);			/* I'm killing the spooler	*/
    XDOS(Q_READ, &mxspl);			/* grab the mx queue	*/
    splbuf.cmd_spl=0x0A;
    splbuf.job_spl=0x00;		/* save the jobs in progress	*/
    XDOS(Q_WRITE, &splin);			/* write the terminate message	*/

    return(SUCCESS);			/* all done		*/
}




do_status()				/* get status on job(s)	*/
/****************************************************************/
/*								*/
/*			DO_STATUS				*/
/*								*/
/****************************************************************/
{

    UWORD	i,j;
    UWORD	k,l;
    struct s_sst	*sstptr;	/* spl status table template	*/


    splbuf.cmd_spl=3;
    splbuf.job_spl=0;
    puts(message[12]);			/* Geting Status ...*/

    if (send_packet()) {
	puts(error[15]);
	return FAILURE;
    }

    if (splbuf.job_spl==0xFF) {
	puts(message[13]);		/* no active jobs	*/
	return SUCCESS;
    }

    goto in_loop;

    while (splbuf.job_spl != 0xFF) {
	splbuf.cmd_spl=3;
	++splbuf.job_spl;
	if (send_packet()) {
	    puts(error[15]);
	    return FAILURE;
	}

in_loop:
	if (splbuf.job_spl!=0xFF) {
	    sstptr=splbuf.dat_spl;	/* template the data buf*/
	    printf(message[8], sstptr->job);
	    printf("%.8s.%.3s ", sstptr->jobname, &sstptr->jobname[8]);

	    switch (sstptr->status) {
	    case 01:
		puts(message[14]);	/* spooling	*/
		break;

	    case 02:			/* waiting to despool	*/
		printf(message[15],
		sstptr->lstnum, sstptr->rcopies,1+((sstptr->osize)/8));
		break;

	    case 03:			/* despooling	*/
		printf(message[16],
		sstptr->lstnum, sstptr->rcopies,1+((sstptr->osize)/8));
		break;

	    case 04:
		puts(message[17]);	/* waiting for a printer*/
		break;

	    case 05:
		puts(message[18]);	/* aborting	*/
		break;
	    } /* end of switch */

	}

    }

    return SUCCESS;
}



/*------------------------------------------------------------------------
	SPOOL UTILITY RUN TIME LIBRARY
------------------------------------------------------------------------*/


send_packet()				/* do a spooler transaction	*/
/****************************************************************/
/*								*/
/*			SEND A SPOOLER TRANSACTION		*/
/*								*/
/****************************************************************/
{

    UWORD	d;


    XDOS(Q_READ, &mxspl);			/* read the mx queue	*/
    XDOS(Q_WRITE, &splin);			/* write the message to splin	*/
    XDOS(Q_READ, &splout);			/* read the response from splout*/
    XDOS(Q_WRITE, &mxspl);			/* put the mx queue back	*/

    if (splbuf.cmd_spl == 0xFF) {
	puts(error[10]);		/* disaster.....	*/
	exit FAILURE;
    }
    return (splbuf.cmd_spl);
}




opt_select(func, pcount, param)
UWORD	func;				/* the function number	*/
UWORD	pcount;				/* parameter count	*/
UBYTE	**param;			/* the control string for parse	*/
/****************************************************************/
/*								*/
/*		SELECT AND PROCESS AN OPTION			*/
/*								*/
/****************************************************************/
{

    UWORD	ret;


    puts("");

    if (!(func == T_HELP || func == T_START))
					/* except on these */

	if (XDOS(Q_OPEN, &mxspl) || XDOS(Q_OPEN, &splin) || XDOS(Q_OPEN, &splout)) {
					/* OPEN THE QUEUES	*/
	    puts(error[00]);		/* no action	*/
	    puts(error[01]);		/* can't get to spl	*/
	    return FAILURE;
	}

    switch (func) {
    case T_PRINT:
	ret=do_print(pcount, param);
	break;

    case T_STATUS:
	ret=do_status();
	break;

    case T_START:
	ret=do_start(pcount, param);
	break;

    case T_DELETE:
	ret=do_delete(pcount, param);
	break;

    case T_HELP:
	ret=do_help();
	break;

    case T_TERMINATE:
	ret=do_terminate();
	break;

    case T_RESET:
	ret=do_reset();
	break;

    default:
	puts(error[02]);		/* invalid verb	*/
	break;
    }

    puts("");

    return ret;
}




get_token(s)
UBYTE	*s;				/* the token string to be found	*/
/****************************************************************/
/*								*/
/*			GET A TOKEN NUMBER			*/
/*								*/
/****************************************************************/
{

    UWORD	ti;		/* token counters	*/
    UBYTE	*t, *save;
/*
*	Entry:	token string for consideration
*	Return:	token number from *token[]
*	0 on no match
*
*
*	Note that the first character in token[0] must be the
*	first character of the token[n+1] where there are n tokens
*	e.g."*"	
*	"toke*n1"	first valid token
*	"tok*en2"	last valid token
*	"*"
*	The token[0][0] character also marks the fewest necessary 
*	characters needed to get a match
*/


    ti=0;				/* token to consider	*/
    save=s;				/* save arg. pointer	*/

    while (*(t=token[++ti]) != *token[0]) {
					/* while tokens left to compare	*/
	while(*(t++) == *(s++))

	    if (*t == *token[0]) {	/* found token marker	*/
		++t;			/* point to next char	*/
s_cmp:
		while(*(t++) == *(s++)) /* rest of strn match ?*/
		    if (*(t-1)==NULL || *(s-1)==NULL)
			break;

		if (*(s-1) == *token[0]) { /* ignore '*'	*/
		    --t;		/* compare t again	*/
		    goto s_cmp;		/* search rest of strn.*/
		}

		if (*(s-1) != NULL)	/* make it to end of str?*/
		    break;

		return ti;		/* ti is token found	*/
	    }
	s=save;				/* restore argument ptr	*/
    }

    return 0;

}
                                                                                                                                                                                                                                                                                 