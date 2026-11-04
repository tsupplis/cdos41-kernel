/* CHKDOSFS -- common checker interface.
 * Native DRI C uses 16-bit unsigned and 32-bit signed long. Decode disk
 * fields explicitly: neither host word size nor structure packing is on disk.
 */
#define SECSIZE 512
#define MAPSIZE 8192
#define MAXDEPTH 32
struct volume {
    unsigned fat16, limit, spc, nfat, fatsiz, roots;
    long fatbase, rootbase, database, sectors;
};
extern struct volume vol;
extern int verbose, failed, repair, wrote;
extern unsigned errors;
extern unsigned wordget(), fatget();
extern int fatset(), fatreset(), wrsect(), repairfs(), confirm();
extern long longget();
extern int rdsect(), fscheck(), geomset(), diskopen(), diskclose();
