/*
 * Behavioral reconstruction of SPL 4.11 from spl.a86.
 * This is new source, not the recovered original SPL.C.
 */
#include "splc.h"

EXTERN UWORD XDOS(), G_SYSDSK();

struct s_sst sst[NSPOOL];
struct s_dst dst[NDEVICE];
struct s_jst jst[NJOB+1];
struct bdos_fcb sfcb[NSPOOL];
UBYTE buffers[NSPOOL][128], ixbuf[128];
UBYTE *dma;
UBYTE sysdrive, nextjob, nextslot, ixactive;
struct s_spl msg, discard;
struct xdos_qpb dspq[NDEVICE];

struct xdos_qd mxqd = {
    0,0,0,1, {'M','X','S','P','L',' ',' ',' '}, 0,1,0,0,0,0,0
};
struct xdos_qd inqd = {
    0,0,0,0, {'S','P','L','I','N',' ',' ',' '}, 160,1,0,0,0,0,0
};
struct xdos_qd outqd = {
    0,0,0,0, {'S','P','L','O','U','T',' ',' '}, 160,1,0,0,0,0,0
};
struct xdos_qpb mxq = {
    0,0,0,0,0, {'M','X','S','P','L',' ',' ',' '}
};
struct xdos_qpb inq = {
    0,0,0,0,(UBYTE *)&msg, {'S','P','L','I','N',' ',' ',' '}
};
struct xdos_qpb outq = {
    0,0,0,0,(UBYTE *)&msg, {'S','P','L','O','U','T',' ',' '}
};
struct bdos_fcb ixfcb = {
    0, {'I','N','D','E','X',' ',' ',' '}, {'D','S','P'}
};
UBYTE spoolnam[] = "SPL.DSP";
UBYTE lstname[] = "LST000: ";
UBYTE dspname[] = "DSP000  ";
UBYTE qerror[] = "There was not enough queue buffer space in your system to start the spooler.\r\n";
struct {
    UBYTE *name;
    struct bdos_fcb *fcb;
} parse;

/* Small byte loops also handle the odd-addressed words in the wire format. */
blcopy(to, from, count)
UBYTE *to, *from;
UWORD count;
{
    while (count--)
        *to++ = *from++;
    return 0;
}

blfill(to, value, count)
UBYTE *to;
UWORD value, count;
{
    while (count--)
        *to++ = value;
    return 0;
}

puttext(text)
UBYTE *text;
{
    while (*text)
        XDOS(C_WRITE, *text++);
    return 0;
}

setdma(buffer)
UBYTE *buffer;
{
    dma = buffer;
    XDOS(F_DMAOFF, buffer);
    return 0;
}

freesp(slot)
UWORD slot;
{
    sst[slot].job = NONE;
    sst[slot].status = 0;
    sst[slot].dma_cnt = 0;
    return 0;
}

freejob(job)
UWORD job;
{
    jst[job].lst_jst = NONE;
    jst[job].pri_jst = 0;
    jst[job].sst_jst = NONE;
    jst[job].dst_jst = NONE;
    return 0;
}

/* Lower numeric priority wins; equal priorities retain arrival order. */
readyin(job)
UWORD job;
{
    UWORD prev, next, n;
    prev = HEAD;
    next = jst[prev].lst_jst;
    for (n = 0; n < NJOB; ++n) {
        if (next == NONE || jst[job].pri_jst < jst[next].pri_jst) {
            jst[prev].lst_jst = job;
            jst[job].lst_jst = next;
            return 0;
        }
        prev = next;
        next = jst[next].lst_jst;
    }
    puttext("SPL: invalid ready list\r\n");
    return 1;
}

UWORD ixread(job)
UWORD job;
{
    setdma(ixbuf);
    ixfcb.r0 = job / 2;
    ixfcb.r1 = ixfcb.r2 = 0;
    return XDOS(F_READRAND, &ixfcb);
}

struct ixentry *ixent(job)
UWORD job;
{
    return (struct ixentry *)(ixbuf + (job & 1) * 64);
}

/* F5 requests the release's partial close, keeping INDEX.DSP available. */
ixsave()
{
    XDOS(F_WRITERAND, &ixfcb);
    ixfcb.fn[4] |= 0x80;
    XDOS(F_CLOSE, &ixfcb);
    return 0;
}

splinit()
{
    UWORD i, made, opened, result;
    struct ixentry *entry;

    if (sizeof(struct s_spl) != 160 || sizeof(struct s_sst) != 24 ||
        sizeof(struct s_dst) != 13 || sizeof(struct s_jst) != 4 ||
        sizeof(struct bdos_fcb) != 36 || sizeof(struct ixentry) != 64 ||
        sizeof(struct xdos_qpb) != 16 || sizeof(struct xdos_qd) != 28) {
        puttext("SPL: incompatible compiler data layout\r\n");
        return 1;
    }
    if (XDOS(Q_MAKE, &outqd) || XDOS(Q_MAKE, &mxqd) ||
        XDOS(Q_MAKE, &inqd)) {
        XDOS(Q_OPEN, &mxq);
        XDOS(Q_OPEN, &inq);
        XDOS(Q_OPEN, &outq);
        XDOS(Q_DELETE, &mxq);
        XDOS(Q_DELETE, &inq);
        XDOS(Q_DELETE, &outq);
        puttext(qerror);
        return 1;
    }
    XDOS(C_DETACH, 0);
    XDOS(Q_OPEN, &mxq);
    XDOS(Q_OPEN, &inq);
    XDOS(Q_OPEN, &outq);
    XDOS(Q_WRITE, &mxq);
    XDOS(F_USERNUM, 0);
    XDOS(F_ERRMODE, 0xff);
    sysdrive = G_SYSDSK() + 1;
    nextjob = nextslot = 0;
    for (i = 0; i < NSPOOL; ++i)
        freesp(i);
    for (i = 0; i < NDEVICE; ++i) {
        dst[i].sta_dst = NONE;
        dst[i].typ_dst = dst[i].frm_dst = 0;
        dst[i].dat_dst = 1;
        blcopy(dst[i].nam_dst, lstname, 8);
        dst[i].nam_dst[3] += i / 100;
        dst[i].nam_dst[4] += (i % 100) / 10;
        dst[i].nam_dst[5] += i % 10;
        dspq[i].bfptr_qp = (UBYTE *)&msg;
        blcopy(dspq[i].name_qp, dspname, 8);
        dspq[i].name_qp[3] += i / 100;
        dspq[i].name_qp[4] += (i % 100) / 10;
        dspq[i].name_qp[5] += i % 10;
        if (XDOS(Q_OPEN, &dspq[i]) == 0)
            dst[i].sta_dst = 0;
    }

    /* A truncated index is deleted and recreated, as in open_index_file. */
    for (;;) {
        opened = 0xffff;
        ixfcb.fn[4] |= 0x80;
        ixfcb.dr = sysdrive;
        made = XDOS(F_MAKE, &ixfcb);
        if (made != 0) {
            if (made != 0x08ff) {
                puttext("SPL: cannot create INDEX.DSP\r\n");
                return 1;
            }
            ixfcb.fn[4] |= 0x80;
            opened = XDOS(F_OPEN, &ixfcb);
            if (opened >= 4) {
                puttext("SPL: cannot open INDEX.DSP\r\n");
                return 1;
            }
        }
        for (i = 0; i <= NJOB; ++i)
            freejob(i);
        setdma(ixbuf);
        if (made == 0) {
            blfill(ixbuf, ' ', 128);
            for (i = 0; i < 127; ++i)
                XDOS(F_WRITE, &ixfcb);
            XDOS(F_CLOSE, &ixfcb);
            ixfcb.ft[1] |= 0x80;
            XDOS(F_ATTRIB, &ixfcb);
            ixfcb.fn[4] |= 0x80;
            XDOS(F_OPEN, &ixfcb);
            nextjob = 0;
            break;
        }
        result = 0;
        for (i = 0; i < NJOB; ++i) {
            if ((i & 1) == 0) {
                result = XDOS(F_READ, &ixfcb);
                if (result)
                    break;
            }
            entry = ixent(i);
            if (entry->stat.status > 1 && entry->stat.status < 5) {
                nextjob = (i + 1) % NJOB;
                entry->stat.status = 2;
                jst[i].pri_jst = entry->stat.prior;
                jst[i].sst_jst = NONE;
                jst[i].dst_jst = entry->stat.lstnum;
                readyin(i);
            }
        }
        if (result == 0)
            break;
        XDOS(F_CLOSE, &ixfcb);
        XDOS(F_DELETE, &ixfcb);
    }
    ixactive = 1;
    XDOS(P_PRIORITY, 200);
    return 0;
}

spstart()
{
    UWORD n, slot, job;
    struct s_sst *s;
    struct bdos_fcb *f;

    if (msg.lst_spl >= NDEVICE || dst[msg.lst_spl].sta_dst == NONE) {
        msg.cmd_spl = 1;
        return 0;
    }
    for (n = 0; n < NSPOOL; ++n)
        if (sst[(nextslot + n) % NSPOOL].job == NONE)
            break;
    if (n == NSPOOL) {
        msg.cmd_spl = 3;
        return 0;
    }
    slot = (nextslot + n) % NSPOOL;
    nextslot = (slot + 1) % NSPOOL;
    for (n = 0; n < NJOB; ++n)
        if (jst[(nextjob + n) % NJOB].pri_jst == 0)
            break;
    if (n == NJOB) {
        msg.cmd_spl = 4;
        return 0;
    }
    job = (nextjob + n) % NJOB;
    nextjob = (job + 1) % NJOB;
    f = &sfcb[slot];
    blfill((UBYTE *)f, 0, 36);
    parse.name = spoolnam;
    parse.fcb = f;
    if (XDOS(F_PARSE, &parse)) {
        msg.cmd_spl = 2;
        return 0;
    }
    f->dr = sysdrive;
    f->fn[3] = 'A' + ((job >> 4) & 15);
    f->fn[4] = 'A' + (job & 15);
    XDOS(F_DELETE, f);
    if (XDOS(F_MAKE, f)) {
        msg.cmd_spl = 2;
        return 0;
    }
    s = &sst[slot];
    s->job = job;
    s->dma_cnt = 0;
    s->status = 1;
    s->lstnum = msg.lst_spl;
    if (msg.nam_spl[0])
        blcopy(s->jobname, msg.nam_spl, 11);
    else
        blcopy(s->jobname, f->fn, 11);
    s->prior = msg.pri_spl ? msg.pri_spl : 128;
    s->flags = msg.flg_spl;
    s->ocopies = msg.cpy_spl ? msg.cpy_spl : 1;
    s->rcopies = s->ocopies;
    s->osize = s->rsize = 0;
    msg.job_spl = job;
    blcopy(msg.nam_spl, s->jobname, 11);
    msg.sta_spl = s->status;
    msg.lst_spl = s->lstnum;
    msg.pri_spl = s->prior;
    msg.cpy_spl = msg.clp_spl = s->ocopies;
    msg.flg_spl = s->flags;
    msg.cmd_spl = 0;
    jst[job].pri_jst = s->prior;
    jst[job].sst_jst = slot;
    jst[job].dst_jst = s->lstnum;
    return 0;
}

/* APPEND is one-way: clients do not read SPLOUT after sending it. */
spdata()
{
    UWORD slot, i;
    struct s_sst *s;
    if (msg.job_spl >= NJOB || jst[msg.job_spl].pri_jst == 0) {
        puttext("SPL: append for unknown job\r\n");
        return 0;
    }
    slot = jst[msg.job_spl].sst_jst;
    if (slot >= NSPOOL || sst[slot].status != 1) {
        puttext("SPL: append for inactive submission\r\n");
        return 0;
    }
    s = &sst[slot];
    if (dma != buffers[slot])
        setdma(buffers[slot]);
    if (msg.byt_spl > 128)
        msg.byt_spl = 128;
    for (i = 0; i < msg.byt_spl; ++i) {
        buffers[slot][s->dma_cnt++] = msg.dat_spl[i];
        if (s->dma_cnt == 128) {
            if (XDOS(F_WRITE, &sfcb[slot]))
                s->flags |= 2;
            s->dma_cnt = 0;
            ++s->osize;
            ++s->rsize;
        }
    }
    return 0;
}

spfinish()
{
    UWORD job, slot;
    struct s_sst *s;
    struct ixentry *entry;
    job = msg.job_spl;
    if (job >= NJOB || jst[job].pri_jst == 0) {
        msg.cmd_spl = 1;
        return 0;
    }
    slot = jst[job].sst_jst;
    if (slot >= NSPOOL || sst[slot].status != 1) {
        msg.cmd_spl = 1;
        return 0;
    }
    s = &sst[slot];
    setdma(buffers[slot]);
    /* Retain dma_cnt and the existing tail bytes: DSP uses the byte count. */
    if (s->dma_cnt) {
        XDOS(F_WRITE, &sfcb[slot]);
        ++s->osize;
        ++s->rsize;
    }
    XDOS(F_CLOSE, &sfcb[slot]);
    sfcb[slot].ft[1] |= 0x80;
    XDOS(F_ATTRIB, &sfcb[slot]);
    s->status = 2;
    if (ixactive != 1) {
        ixfcb.fn[4] |= 0x80;
        XDOS(F_OPEN, &ixfcb);
        ixactive = 1;
    }
    ixread(job);
    entry = ixent(job);
    blcopy((UBYTE *)&entry->stat, (UBYTE *)s, 24);
    blcopy((UBYTE *)&entry->fcb, (UBYTE *)&sfcb[slot], 36);
    ixsave();
    freesp(slot);
    readyin(job);
    jst[job].sst_jst = NONE;
    msg.job_spl = job;
    msg.cmd_spl = (s->flags & 2) ? 2 : 0;
    return 0;
}

spabort()
{
    UWORD job, slot, prev, next, n, found;
    struct ixentry *entry;
    job = msg.job_spl;
    if (job >= NJOB || jst[job].pri_jst == 0) {
        msg.cmd_spl = 1;
        return 0;
    }
    slot = jst[job].sst_jst;
    if (slot != NONE) {
        XDOS(F_CLOSE, &sfcb[slot]);
        XDOS(F_DELETE, &sfcb[slot]);
        freesp(slot);
        freejob(job);
    } else {
        prev = HEAD;
        next = jst[prev].lst_jst;
        found = 0;
        for (n = 0; n < NJOB && next != NONE; ++n) {
            if (next == job) {
                jst[prev].lst_jst = jst[next].lst_jst;
                jst[job].lst_jst = NONE;
                found = 1;
                break;
            }
            prev = next;
            next = jst[next].lst_jst;
        }
        ixread(job);
        entry = ixent(job);
        if (found) {
            XDOS(F_DELETE, &entry->fcb);
            blfill((UBYTE *)entry + 1, ' ', 63);
            ixsave();
            freejob(job);
        } else {
            dst[jst[job].dst_jst].sta_dst = 4;
            entry->stat.status = 5;
            ixsave();
        }
    }
    msg.cmd_spl = 0;
    return 0;
}

spstatus()
{
    struct ixentry *entry;
    if (!ixactive) {
        msg.cmd_spl = 0;
        msg.job_spl = NONE;
        return 0;
    }
    if (msg.job_spl > NJOB) {
        msg.cmd_spl = 1;
        return 0;
    }
    if (ixread(msg.job_spl) & 0xff) {
        msg.cmd_spl = 1;
        return 0;
    }
    while (msg.job_spl != NJOB) {
        if ((msg.job_spl & 1) == 0 &&
            ixfcb.r0 != msg.job_spl / 2) {
            if (ixread(msg.job_spl) & 0xff) {
                msg.cmd_spl = 1;
                return 0;
            }
        }
        entry = ixent(msg.job_spl);
        if (entry->stat.jobname[0] != ' ' &&
            entry->stat.jobname[0] != 0) {
            blcopy(msg.dat_spl, (UBYTE *)entry, 64);
            msg.cmd_spl = 0;
            return 0;
        }
        ++msg.job_spl;
    }
    msg.cmd_spl = 0;
    msg.job_spl = NONE;
    return 0;
}

spstop()
{
    UWORD mode, i, half;
    struct ixentry *entry;
    mode = msg.job_spl;
    XDOS(P_PRIORITY, 100);
    for (i = 0; i < NDEVICE; ++i) {
        if (dst[i].sta_dst <= 4) {
            XDOS(Q_CREAD, &dspq[i]);
            msg.cmd_spl = 10;
            msg.job_spl = mode;
            XDOS(Q_CWRITE, &dspq[i]);
        }
    }
    while (XDOS(Q_DELETE, &inq))
        while (XDOS(Q_CREAD, &inq) == 0)
            ;
    msg.cmd_spl = 0;
    while (XDOS(Q_DELETE, &mxq))
        XDOS(P_DELAY, 60);
    XDOS(Q_DELETE, &outq);
    if (mode != 1)
        return 0;
    if (!ixactive)
        XDOS(F_OPEN, &ixfcb);
    setdma(ixbuf);
    for (i = 0; i < 127; ++i) {
        ixfcb.r0 = i;
        ixfcb.r1 = ixfcb.r2 = 0;
        if (XDOS(F_READRAND, &ixfcb) & 0xff)
            break;
        for (half = 0; half < 2; ++half) {
            entry = ixent(half);
            if (entry->fcb.dr != ' ')
                XDOS(F_DELETE, &entry->fcb);
        }
    }
    XDOS(F_CLOSE, &ixfcb);
    XDOS(F_DELETE, &ixfcb);
    for (i = 0; i < NSPOOL; ++i) {
        if (sst[i].status == 1) {
            XDOS(F_CLOSE, &sfcb[i]);
            XDOS(F_DELETE, &sfcb[i]);
        }
    }
    return 0;
}

spevent()
{
    UWORD job;
    job = msg.job_spl;
    if (job >= NJOB || jst[job].dst_jst >= NDEVICE) {
        puttext("SPL: event for unknown job\r\n");
        return 0;
    }
    ixread(job);
    blfill((UBYTE *)ixent(job) + 1, ' ', 63);
    ixsave();
    blcopy((UBYTE *)&dst[jst[job].dst_jst], msg.dat_spl, 13);
    freejob(job);
    return 0;
}

spreport()
{
    UWORD device;
    struct ixentry *entry;
    if (msg.job_spl >= NJOB ||
        jst[msg.job_spl].dst_jst >= NDEVICE) {
        puttext("SPL: report for unknown job\r\n");
        return 0;
    }
    device = jst[msg.job_spl].dst_jst;
    if (dst[device].sta_dst == 4) {
        msg.sta_spl = NONE;
    } else {
        if (msg.sta_spl == 1) {
            ixread(msg.job_spl);
            entry = ixent(msg.job_spl);
            --entry->stat.rcopies;
            ixsave();
        } else if (msg.sta_spl == 2) {
            dst[device].sta_dst = 3;
        }
        msg.sta_spl = 0;
    }
    msg.cmd_spl = 1;
    XDOS(Q_WRITE, &dspq[device]);
    return 0;
}

spsend()
{
    UWORD i;
    for (;;) {
        for (i = 0; i < 6; ++i) {
            if (XDOS(Q_CWRITE, &outq) == 0)
                return 0;
            XDOS(P_DELAY, 10);
        }
        outq.bfptr_qp = (UBYTE *)&discard;
        XDOS(Q_CREAD, &outq);
        outq.bfptr_qp = (UBYTE *)&msg;
    }
}

spsched()
{
    UWORD prev, next, n, device;
    struct ixentry *entry;
    prev = HEAD;
    next = jst[prev].lst_jst;
    for (n = 0; n < NJOB && next != NONE; ++n) {
        device = jst[next].dst_jst;
        if (device >= NDEVICE) {
            puttext("SPL: invalid device in saved job\r\n");
            return 1;
        }
        if (dst[device].sta_dst == 0) {
            msg.cmd_spl = 0;
            msg.job_spl = next;
            ixread(next);
            entry = ixent(next);
            entry->stat.status = 3;
            blcopy(msg.dat_spl, (UBYTE *)entry, 64);
            ixsave();
            XDOS(Q_WRITE, &dspq[device]);
            dst[device].sta_dst = 1;
            jst[next].dst_jst = device;
            next = jst[next].lst_jst;
            jst[jst[prev].lst_jst].lst_jst = NONE;
            jst[prev].lst_jst = next;
        } else {
            prev = next;
            next = jst[next].lst_jst;
        }
    }
    if (jst[HEAD].lst_jst == NONE) {
        for (device = 0; device < NDEVICE; ++device)
            if (dst[device].sta_dst != NONE && dst[device].sta_dst > 0)
                return 0;
        ixactive = 0;
        XDOS(F_CLOSE, &ixfcb);
    }
    return 0;
}

splrun()
{
    UWORD command;
    if (splinit())
        return 1;
    spsched();
    for (;;) {
        XDOS(Q_READ, &inq);
        command = msg.cmd_spl;
        switch (command) {
        case 0:
            spstart();
            break;
        case 1:
            spdata();
            continue;
        case 2:
            spabort();
            break;
        case 3:
            spstatus();
            break;
        case 7:
            spfinish();
            break;
        case 10:
            spstop();
            return 0;
        case 16:
            spevent();
            spsched();
            continue;
        case 17:
            spreport();
            continue;
        default:
            msg.cmd_spl = NONE;
            break;
        }
        spsend();
        if (command == 7)
            spsched();
    }
}

main()
{
    return splrun();
}

_main()
{
    main();
    XDOS(0, 0);
    return 0;
}
