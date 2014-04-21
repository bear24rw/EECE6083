#include <stdio.h>
#include "runtime.h"

int R[NUM_REGS];
int M[MEM_SIZE];
int SP = 0;
int FP = 0;

void putInteger(int x)
{
    printf("%d\n", x);
}

void putBool(int x)
{
    x ? printf("true") : printf("false");
}
