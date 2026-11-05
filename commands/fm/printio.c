/* CDOS list ownership: the original uses conditional attach (161),
 * list output (5) and detach (159), on the current logical printer.
 * There is no DOS spooler dependency or printer-number override.
 */
#include "printjob.h"
int BDOS();
static int attach()
{
    return (BDOS(161,0)&255)==0;
}
static int detach()
{
    BDOS(159,0);return 1;
}
static int put(ch)
int ch;
{
    BDOS(5,ch&255);return 1;
}
static int key()
{
    if(!(BDOS(6,254)&255)) return 0;
    BDOS(6,253);return 1;
}
int fm_printer_native(printer,notice)
struct fm_printer *printer;
int (*notice)();
{
    printer->attach=attach;printer->detach=detach;printer->put=put;
    printer->key=key;printer->notice=notice;
    return 1;
}
