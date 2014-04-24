#include <stdio.h>
#include "runtime.h"

int R[NUM_REGS];
int M[MEM_SIZE];
int SP = 0;
int FP = 0;
float tmp_float;
char tmp_string[MAX_STR_LEN];

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
    printf("%s", (char*)&M[x]);
}

void putFloat(float x)
{
    printf("%f", x);
}

int getInteger()
{
    int x;
    scanf("%d", &x);
    return x;
}

float getFloat()
{
    float x;
    scanf("%f", &x);
    return x;
}

void getString()
{
    fgets(tmp_string, MAX_STR_LEN, stdin);
}
