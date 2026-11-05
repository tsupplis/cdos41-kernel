/* FM reconstruction: portable configuration core, DR C small model.
 * Keep native disk, terminal and process interfaces outside this module.
 */
#define FM_CONFIG_COUNT 16
struct fm_config {
    char value[FM_CONFIG_COUNT];
};
extern char *fm_config_names[];
int fm_config_keyword();
int fm_config_number();
int fm_config_assignment();

/* Incremental record-independent configuration input; Ctrl-Z ends text. */
struct fm_config_reader {
    char line[82];
    int used, overflow, ended, assignments;
};
int fm_config_defaults();
int fm_config_begin();
int fm_config_feed();
int fm_config_finish();
int fm_config_load();
