/* ask(name,target): max 15 chars, 1 input, 0 skip, -1 cancel, -2 UI error.
 * transfer(source,raw,destination,targetraw,dma,cancel): 1/0/-1.
 * report(message): nonzero on success. Source entries never change.
 */
struct fm_named_copier { int (*ask)(); int (*transfer)();
                         int (*cancel)(); int (*report)(); };
/* 1 processed (possibly skipped), 0 cancelled, -1 error. */
int fm_copy_names();
/* Destination of last attempted transfer, or source before any transfer. */
int fm_copy_name_drive();
