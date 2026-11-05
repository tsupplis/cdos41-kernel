/* Subset input and matching are independent of screen and disk access. */
struct fm_input { char text[13]; int length,active; };
int fm_input_open();
int fm_input_key();
int fm_subset_match();
int fm_native_subset();
unsigned fm_native_drives();
int fm_native_drive();
