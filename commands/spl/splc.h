/* Wire/disk layouts from ../dsp/spldef.h; DRC uses byte-aligned words. */
#include <portab.h>

#define NSPOOL 8
#define NDEVICE 16
#define NJOB 254
#define NONE 0xff
#define HEAD 254

#define C_WRITE 2
#define C_DETACH 147
#define F_OPEN 15
#define F_CLOSE 16
#define F_DELETE 19
#define F_READ 20
#define F_WRITE 21
#define F_MAKE 22
#define F_DMAOFF 26
#define F_ATTRIB 30
#define F_USERNUM 32
#define F_READRAND 33
#define F_WRITERAND 34
#define F_ERRMODE 45
#define F_PARSE 152
#define Q_MAKE 134
#define Q_OPEN 135
#define Q_DELETE 136
#define Q_READ 137
#define Q_CREAD 138
#define Q_WRITE 139
#define Q_CWRITE 140
#define P_DELAY 141
#define P_PRIORITY 145

struct s_spl {
    UBYTE cmd_spl, job_spl, nam_spl[11], sta_spl;
    UBYTE lst_spl, pri_spl, flg_spl, cpy_spl, clp_spl;
    UWORD siz_spl, slp_spl, byt_spl;
    UBYTE rsv_spl[7], dat_spl[128];
};

struct s_sst {
    UBYTE job, jobname[11], status, lstnum, prior, flags;
    UBYTE ocopies, rcopies;
    UWORD osize, rsize, dma_cnt;
};

struct s_dst {
    UBYTE sta_dst, nam_dst[8], typ_dst, frm_dst;
    UWORD dat_dst;
};

struct s_jst {
    UBYTE lst_jst, pri_jst, sst_jst, dst_jst;
};

struct bdos_fcb {
    UBYTE dr, fn[8], ft[3], ex, s1, s2, rc;
    UBYTE dm[16], cr, r0, r1, r2;
};

struct xdos_qpb {
    UBYTE flg_qp, net_qp;
    UWORD qadr_qp, nmsgs_qp;
    UBYTE *bfptr_qp;
    UBYTE name_qp[8];
};

struct xdos_qd {
    UWORD link_qd;
    UBYTE net_qd, org_qd;
    UWORD flg_qd;
    UBYTE name_qd[8];
    UWORD len_qd, nmsg_qd, dqph_qd, nqph_qd;
    UWORD mcnt_qd, mout_qd, bfpt_qd;
};

struct ixentry {
    struct s_sst stat;
    struct bdos_fcb fcb;
    UBYTE pad[4];
};
