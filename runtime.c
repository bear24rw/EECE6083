#include <stdio.h>
#include "runtime.h"

int R[NUM_REGS];
int M[MEM_SIZE];
int SP = MEM_SIZE-1;

void putInteger(int x)
{
    printf("%d", x);
}

void putBool(int x)
{
    x ? printf("true") : printf("false");
}
