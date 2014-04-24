#include <stdio.h>
#include "runtime.h"

int R[NUM_REGS];
int M[MEM_SIZE];
int SP = 0;
int FP = 0;
float tmp_float;

void putInteger(int x)
{
    printf("%d", x);
}

void putBool(int x)
{
    x ? printf("true") : printf("false");
}

void putString(int x)
{
    while (M[x]) printf("%c", M[x++]);
}

void putFloat(float x)
{
    printf("%f", x);
}
