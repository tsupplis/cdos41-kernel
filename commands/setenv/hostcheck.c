#include <assert.h>
#include <string.h>
#include "setenv.h"
#undef main
int main(void)
{
    memset(envbuf,0,sizeof envbuf);
    memcpy(envbuf,"PATH=X\0OS=CDOS\0",15);
    assert(change("temp",4,"Mixed Case path",1024)==0);
    assert(memcmp(result,"PATH=X\0OS=CDOS\0TEMP=Mixed Case path\0\0",36)==0);
    memcpy(envbuf,result,1024);
    assert(change("TeMp",4,"Replacement",1024)==0);
    assert(memcmp(result,"PATH=X\0OS=CDOS\0TEMP=Replacement\0\0",33)==0);
    assert(change("TeMp",4,"",1024)==0);
    assert(memcmp(result,"PATH=X\0OS=CDOS\0\0",16)==0);
    assert(change("PATH",4,"long value",16)==-1);
    assert(strstr(envbuf,"PATH=X")==envbuf);
    memset(envbuf,'x',1024);
    assert(envused(envbuf,1024)==-1);
    memset(envbuf,0,1024);
    assert(change("A",1,"1234",8)==0);
    assert(change("A",1,"12345",8)==-1);
    return 0;
}
