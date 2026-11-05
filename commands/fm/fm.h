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
