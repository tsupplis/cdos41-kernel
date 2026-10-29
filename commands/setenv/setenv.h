#define main MAIN
#define tailread TAILREAD
#define bdos BDOS
#define envread ENVREAD
#define envwrite ENVWRITE
#define ENV_MAX 1024
extern char envbuf[ENV_MAX], result[ENV_MAX];
int tailread(), bdos(), envread(), envwrite(), envused(), change();
