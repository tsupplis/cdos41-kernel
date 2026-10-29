/************************************************************************
*									*
*    NETWORK DESPOOLER PROCESS						*
*									*
*************************************************************************
*									*
*    Created	7 October 1983				   		*
*    By	Kevin Schoch				     			*
*									*
*************************************************************************

    History:

    12/06/83    Transmuted into a cmd type program from rsp
    01/11/84    Copies option added
    01/16/84    strings removed to dspm.c

*************************************************************************/

/*
	    **************************
	    *   COPYRIGHT (C) 1984   *
	    *  DIGITAL RESEARCH INC. *
	    *      P.O. BOX 579      *
	    *    PACIFIC GROVE, CA   *
	    *	     93950	     *
	    **************************
*/

/*-------------------------------------
    INCLUDE FILES
-------------------------------------*/

#include    "stdio.h"



#include	"cpmcall.h"



#include    "spldef.h"




#define	USER_NUM    0
#define	RTP	8			/* records to read and print    */


/*-------------------------------------
    EXTERNAL DEFINITIONS
-------------------------------------*/

struct    s_spl    dspbuf;		/* despooler queue message buf	*/

EXTERN    struct xdos_qpb splin;	/* spooler process input queue	*/
EXTERN    struct xdos_qd dspqd;		/* despooler queue descriptor	*/
EXTERN    struct xdos_qpb dspin;	/* despooler command queue	*/

EXTERN    UBYTE lst_name[];		/* default list device name	*/
EXTERN    UBYTE dm0[], dm1[], dm2[], dm3[]; /* user messages		*/

struct    bdos_fcb  dspfcb;		/* despooler file control block	*/
UBYTE    dma_buf[RTP*128];		/* set RTP record dma buffer	*/
struct    s_dst    dst;			/* despooler status table	*/
struct    s_sst    sst;			/* spooler job status entry	*/

struct    s_chcb {			/* character control block for lst:*/
    UBYTE    *strn_off;
    UBYTE    *strn_seg;
    UWORD    char_cnt;
}chcb;




EXTERN    UWORD    XDOS();
EXTERN    UWORD    GETDS();		/* get your current data seg    */



_main()
{
    main();
    return;
}


main()
{
    dsp();
}



dsp()
/****************************************************************/
/*								*/
/*    DESPOOL FROM A TEMPORARY FILE TO A LIST DEVICE		*/
/*								*/
/****************************************************************/
{
    REG  UWORD  i,j;			/* most used indeces	    	*/
    UWORD    k,l;			/* general purpose indeces	*/
    UBYTE    *cpyptr0, *cpyptr1;	/* general purpose byte transfer pointer*/
    UBYTE    state;	    		/* internal state of the despooler    */
					/* 0 = ready, 1 = waiting on lst:, 2 = init lst:*/
					/* 3 = printing, 4 = closeup	*/
    UBYTE    read_done;


/*-------------------------------------
    INITIALIZATION
-------------------------------------*/
    XDOS(F_ERRMODE, 0xFF);			/* set return error mode	*/
    XDOS(P_PRIORITY, 49);			/* boost priority    		*/

    i = XDOS(L_GET);			/* this is our rsp num.    	*/
    dspqd.name_qd[3] = (i/100)+'0';	/* set up queue name    	*/
    dspqd.name_qd[4] = ((i%100)/10)+'0';
    dspqd.name_qd[5] = (i%10)+'0';
    dspin.name_qp[3] = (i/100)+'0';
    dspin.name_qp[4] = ((i%100)/10)+'0';
    dspin.name_qp[5] = (i%10)+'0';

    if (XDOS(Q_MAKE, &dspqd)) {		/* make the dsp queue    	*/
	XDOS(C_WRITESTR, dm0);			/* couldn't make queue    	*/
	XDOS(C_WRITESTR, dm1);
	XDOS(C_WRITESTR, dm2);
	XDOS(C_WRITESTR, dm1);
	return;				/* exit on failure    		*/
    }

    XDOS(Q_OPEN, &dspin);		/* open the dsp queue    	*/
    XDOS(C_WRITESTR, dm3);			/* write success    		*/
    XDOS(C_DETACH);				/* give up the console    	*/
    XDOS(C_SET, 0);			/* console is 0			*/
    XDOS(F_USERNUM, USER_NUM);			/* set the user number    	*/
    XDOS(145, 200);			/* reset priority    		*/

    l = 0;
    while (XDOS(Q_OPEN, &splin)) {		/* open    spooler in queue	*/
	if (++l < 16)
	    XDOS(P_DELAY, 60);		/* delay and try again     	*/
        else {
	    XDOS(Q_DELETE, &dspin);		/* couldn't find spooler	*/
	    return;
	}
    }

    state = 0x00;			/* state is ready    		*/

    dst.sta_dst = 0x00;			/* stati  =  unused    		*/
    dst.typ_dst = 0;			/* default			*/
    dst.dat_dst = 1;			/* default # of K bytes    	*/
    dst.frm_dst = 0;			/* default type			*/
    dst.nam_dst[0] = lst_name[0];	/* default name			*/
    dst.nam_dst[1] = lst_name[1];	/* default name			*/
    dst.nam_dst[2] = lst_name[2];	/* default name			*/
    dst.nam_dst[3] = (i/100)+lst_name[3];/* default name		*/
    dst.nam_dst[4] = ((i%100)/10)+lst_name[4];/* default name		*/
    dst.nam_dst[5] = (i%10)+lst_name[5];/* default name			*/
    dst.nam_dst[6] = lst_name[6];	/* default name			*/
    dst.nam_dst[7] = lst_name[7];	/* default name			*/

    chcb.strn_off = dma_buf;		/* string offset for lst:	*/
    chcb.strn_seg = GETDS();		/* get the data segment		*/

/*-------------------------------------
    READ DESPOOLER COMMAND QUEUE
-------------------------------------*/
get_command:

    XDOS(Q_READ, &dspin);			/* hang on command queue	*/

/*-------------------------------------
    PROCESS COMMAND
-------------------------------------*/
do_command:

    switch (dspbuf.cmd_spl) {
    case 0x00:				/* new job command		*/
        if (dst.sta_dst != 0x00)	/* status must be ready		*/
	    goto end_data;		/* no, ignore the message	*/

	cpyptr0 = dspbuf.dat_spl;	/* unpack the message		*/
	cpyptr1 = &sst;
	for (i = 0; i<sizeof(sst); i++)	/* copy in job status		*/
	    cpyptr1[i] = cpyptr0[i];
	cpyptr1 = &dspfcb;
	for (i = 0; i<36; i++)		/* copy in the fcb		*/
	    cpyptr1[i] = cpyptr0[i+sizeof(sst)];

	dst.sta_dst = 0x01;		/* despooler is busy now	*/
	break;

    case 0x01:				/* response from spooler	*/
	if (dst.sta_dst != 0x01)	 /* status must be busy		*/
	    goto end_data;		/* ignore the message		*/
	if (dspbuf.sta_spl == 0x00) {	/* successful return		*/
	    switch (state) {
	    case 0x00:			/* this shouldn't occur		*/
		state = 0x04;		/* do a close up		*/
		goto do_command;	/* reprocess the command	*/

	    case 0x01:			/* waiting for lst:		*/
		goto get_lst;

	    case 0x02:			/* init. print file		*/
		goto start_print;

	    case 0x03:			/* printing			*/
		goto printing;

	    case 0x04:			/* closing up			*/
		goto end_data;

	    case 0x05:			/* finnished a copy		*/
		goto new_copy;
	    }
	}
	if (dspbuf.sta_spl == 0xFF) {	/* unsuccessful return		*/
	    XDOS(F_CLOSE, &dspfcb);		/* close the file		*/
	    XDOS(F_DELETE, &dspfcb);		/* delete the file		*/
	    dst.sta_dst = 0x00;		/* despooler is ready		*/
	    state = 0x00;		/* state is ready		*/
	    XDOS(L_DETACH);			/* let go of the printer	*/
	    dspbuf.cmd_spl = 0x10;	/* despooler event		*/
	    dspbuf.job_spl = sst.job;	/* indentify the job #		*/
	    dspbuf.sta_spl = 0x00;	/* event = job completion	*/
	    cpyptr0 = &dst;		/* point to dsp. status		*/
	    for (i = 0; i<sizeof(dst); i++)/* copy despooler status	*/
		dspbuf.dat_spl[i] = cpyptr0[i];/* table back		*/
	    XDOS(Q_WRITE, &splin);		/* write the message		*/
	    goto get_command;		/* get next command		*/
	}
	else
	    goto end_data;		/* bizzare error		*/

    case 0x02:				/* configuration change		*/
	if (dst.sta_dst!= 0x00)	/* status must be ready		*/
	   goto end_data;
 	cpyptr1 = &dst;
 	for (i = 0; i<sizeof(dst); i++)	/* copy in new config.		*/
	    cpyptr1[i] = dspbuf.dat_spl[i];
	dst.sta_dst = 0x00;		/* status is still ready	*/
	goto get_command;

    case 0x03:				/* report configuration		*/
	cpyptr0 = &dst;
	for (i = 0; i<sizeof(dst); i++)	/* copy dst entry		*/
	    dspbuf.dat_spl[i] = cpyptr0[i];
	dspbuf.cmd_spl = 0x10;		/* despooler event		*/
	dspbuf.sta_spl = 0x01;		/* status report		*/
	dspbuf.job_spl = sst.job;	/* this job's number		*/
	XDOS(Q_WRITE, &splin);		/* write message		*/
	goto get_command;

    case 0x08:				/* disable the despooler	*/
	if (dst.sta_dst != 0x00)	/* status must be ready		*/
	    goto end_data;
	dst.sta_dst = 0x02;		/* status  =  diabled		*/
	goto get_command;

    case 0x09:				/* enable despooler		*/
	if (dst.sta_dst != 0x02)	/* must be disabled		*/
	    goto end_data;
	dst.sta_dst = 0x00;		/* set to re		*/
	goto get_command;

    case 0x0A:				/* terminate despooler		*/ 
	XDOS(Q_DELETE, &dspin);		/* delete input queue		*/
	if (dspbuf.job_spl  ==  1) {
	    XDOS(F_CLOSE, &dspfcb);		/* close any file		*/
	    XDOS(F_DELETE, &dspfcb);		/* delete any file		*/
	}
	return;				/* terminate process		*/

    default:				/* no other despooler		*/
	goto end_data;			/* commands are defined		*/
    }


/*-------------------------------------
    GET THE LIST DEVICE
-------------------------------------*/
get_lst:
    state = 0x01;			/* waiting on lst:		*/

    if (XDOS(L_CATTACH)) {			/* cond. attach lst:		*/
	dspbuf.cmd_spl = 0x11;		/* report dsp status		*/
	dspbuf.sta_spl = 0x02;		/* unable to attach		*/
	dspbuf.job_spl = sst.job;	/* this job number		*/
	XDOS(Q_WRITE, &splin);		/* write message to spl		*/
	XDOS(P_DELAY, 300);			/* delay 5 seconds		*/
	goto get_command;		/* get response			*/
    }

/*-------------------------------------
    INITIALIZE FOR LIST OUTPUT
-------------------------------------*/
start_print:
    state = 0x02;			/* init. of print file		*/
    dspfcb.r0 = 0;
    dspfcb.r1 = 0;
    dspfcb.r2 = 0;
    dspfcb.ex = 0;
    dspfcb.cr = 0;

    if ((XDOS(F_OPEN, &dspfcb)&0x00FF) == 0xFF)
					/* open the file		*/
	goto end_data;			/* on failure abort		*/


/*---------------------------
     START COPY
---------------------------*/

    while (sst.rcopies !=  0) {		/* copies left ???		*/
	UWORD rcount;

	sst.rcopies--;
	XDOS(F_DMAOFF, dma_buf);		/* set the dma buffer		*/
	XDOS(F_MULTISEC, RTP);			/* set the multi sect.		*/

	dspfcb.r0 = 0;
	dspfcb.r1 = 0;
	dspfcb.r2 = 0;
	XDOS(F_READRAND, &dspfcb);
	dspfcb.cr = 0;

/*---------------------------
     PRINT DATA TO LST:
---------------------------*/

	i = 0;				/* init. record count		*/

put_data:
	state = 0x03;			/* printing data		*/


/***************************************
* A routine could be included here to  *
* print a header banner.  Flag zero in *
* sst flag field has been reserved for *
* this purpose.			*
***************************************/ 

	rcount = 0;
	i = 0;				/* count the blocks		*/
	read_done = FALSE;

	do {
	    l = XDOS(F_READ, &dspfcb);	/* read a block			*/
	    k = ((l>>8)&0x00FF);	/* records read			*/
	    l &=  0x00FF;		/* error code			*/

	    switch (l)	{		/* read a block			*/
	    case 00:
		rcount +=  RTP;
		if (rcount  ==  sst.osize)
		    chcb.char_cnt = 128*(RTP-1)+sst.dma_cnt;
		else
		    chcb.char_cnt = RTP*128;
		break;
	    case 01:
		if (k == 0)		/* on no records read		*/
		    goto end_copy;
		if (sst.dma_cnt)	/* if on even rec. count	*/
		    chcb.char_cnt = 128*(k-1)+sst.dma_cnt;
		else
		    chcb.char_cnt = 128*k;
		read_done = TRUE;
		break;

	    default:    
		goto end_data;		/* file sys. error		*/
	    };

	    chcb.strn_off = dma_buf;	/* characters location		*/
	    XDOS(L_WRITEBLK, &chcb);	/* print data			*/

	    if (++i == dst.dat_dst) {	/* ready to report ???		*/
		i = 0;
		dspbuf.cmd_spl = 0x11;	/* despooler event		*/
		dspbuf.job_spl = sst.job;/* job number			*/
		dspbuf.sta_spl = 0x00;	/* print progress report	*/
		dspbuf.siz_spl = k*RTP;	/* records printed		*/
		XDOS(Q_WRITE, &splin);	/* write message		*/
		goto get_command;
	    }

printing:				/* return here			*/
	}  while (read_done == FALSE);

/*---------------------------
     END OF COPY
---------------------------*/
end_copy:
	state = 0x05;
	dspbuf.cmd_spl = 0x11;		/* despooler event		*/
	dspbuf.job_spl = sst.job;	/* job number			*/
	dspbuf.sta_spl = 0x01;		/* copy finished		*/
	XDOS(Q_WRITE, &splin);		/* write message		*/
	goto get_command;

new_copy:		    		/* return herE			*/
    } /* END of COPIES LOOP    */


/*---------------------------
     END OF PRINTING
---------------------------*/

end_data:
    state = 0x04;			/* close up system		*/

    dspbuf.cmd_spl = 0x01;		/* pretend to report from	*/
    dspbuf.sta_spl = 0xFF;		/* spooler, order an abort	*/
    goto do_command;			/* do pretend command		*/
}
                                                                                                                                                                                                                                                                                                                              