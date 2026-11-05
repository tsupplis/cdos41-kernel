/* Original menu descriptors, translated from DATA 1C1E/1C40 and 1C56/1C78.
 * Order, spelling and selection bounds are part of the reference interface.
 * No operation is executed here; the future event loop dispatches action IDs.
 */
#include "menu.h"
struct fm_menu_item fm_menu_items[] = {
    { "help", "Help", "Concurrent DOS Help System", "HELP", 0, 32767 },
    { "directory", "File  Directory", "Change to another file directory", "*DIRECTORY", 0, 32767 },
    { "subset", "Subset of Files", "Display files matching a wildcard specification", "*SUBSET", 0, 32767 },
    { "drive", "Drive Selection", "Change drives", "*DRIVE", 0, 32767 },
    { "type", "Type   File(s)", "Display contents of one or more files", "*TYPE", 1, 32767 },
    { "print", "Print  File(s)", "one or more files", "*PRINT", 1, 32767 },
    { "copy", "Copy   File(s)", "one or more files", "*COPY", 1, 32767 },
    { "rename", "Rename File(s)", "one or more files", "*RENAME", 1, 32767 },
    { "delete", "Delete File(s)", "one or more files", "*DELETE", 1, 32767 },
    { "backup", "Backup File(s)", "Backup and Restore your hard disk files", "BACK", 0, 32767 },
    { "edit", "Edit a File", "Edit a file", "DREDIX", 0, 1 },
    { "run", "Run  a Program", "Run a program of type  .BAT, .EXE, .COM or .CMD", "*RUN", 1, 1 },
    { "disk_copy", "Copy   Diskette", "Make a duplicate copy of a diskette", "DSKMAINT DISKCOPY", 0, 32767 },
    { "disk_format", "Format Diskette", "Format a floppy diskette for use with Concurrent DOS", "DSKMAINT FORMAT", 0, 32767 },
    { "free_memory", "Free   Memory", "Display or stop programs that are running", "FREEMEMORY", 0, 32767 },
    { "toggle_details", "Size/Date ON ", "Switch between long and short directory displays", "*CHANGEDIR", 0, 32767 },
    { "setup_menu", "Set Up System", "Setup Concurrent System Defaults", "*SETUPSYSTEM", 0, 32767 },
    { "copy_system", "Copy to Sys Disk", "Place programs for system wide access", "*SETUPSYSTEM SYSTEMDISK", 1, 32767 },
    { "system_attributes", "System Attributes", "Set file(s) for system wide read/only access", "*SETUPSYSTEM ATTRIBUTES", 1, 32767 },
    { "local_attributes", "Local  Attributes", "Set file(s) for local read/write access", "*SETUPSYSTEM ATTRIBUTES", 1, 32767 },
    { "load_function_keys", "Load   Func Keys", "reads a file containing function key assignments", "*SETUPSYSTEM LOADFUNCKEYS", 1, 1 },
    { "assign_function_keys", "Assign Func Keys", "Assign Concurrent commands to the function keys", "FUNCTION", 0, 32767 },
    { "serial_ports", "Serial Ports", "Set up the Serial Ports", "SETPORT", 0, 32767 },
    { "system_defaults", "System Defaults", "Set up the system defaults", "SETUP", 0, 32767 },
    { "memory_disk", "Memory Disk", "Set up a memory disk", "SETUP MDISK", 0, 32767 },
    { "boot_hard_disk", "Boot From H D", "Boot Concurrent from the hard disk", "HDMAINT BOOT", 0, 32767 },
    { "hard_disk_maintenance", "Hard Disk Maint", "Format, verify, change partitions, etc.", "HDMAINT", 0, 32767 },
    { "diskette_maintenance", "Diskette  Maint", "Format, verify and copy diskettes", "DSKMAINT", 0, 32767 },
};
int fm_menu_count = 28;
int fm_file_menu_count = 17;
