/* Subset dialog bound from CODE 3A46h; wildcard semantics are delegated
 * to native BDOS 152, just as CODE 2281h does. Match the resulting 8.3 mask.
 */
#include "select.h"
int fm_input_open(input)
struct fm_input *input;
{
    input->length=0;input->text[0]=0;input->active=1;return 1;
}
/* -1 cancel, 0 ignore, 1 edit, 2 submit. No partial edit reaches the filter. */
int fm_input_key(input,key)
struct fm_input *input;
int key;
{
    if(!input || !input->active) return 0;
    if(key==27) {input->active=0;return -1;}
    if(key==13) return 2;
    if(key==8 || key==127) {
        if(!input->length) return 0;
        input->text[--input->length]=0;return 1;
    }
    if(key<32 || key>126 || input->length==12) return 0;
    input->text[input->length++]=key;input->text[input->length]=0;return 1;
}
int fm_subset_match(mask,entry)
char *mask,*entry;
{
    int i;
    if(!mask || !entry) return 0;
    for(i=0;i<11;++i)
        if(mask[i]!='?' && (mask[i]&127)!=(entry[i+1]&127)) return 0;
    return 1;
}
