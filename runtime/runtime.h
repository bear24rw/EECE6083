#ifndef __RUNTIME_H__
#define __RUNTIME_H__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NUM_REGS  10000
#define MEM_SIZE  10000
#define MAX_STR_LEN 100

extern int R[NUM_REGS];
extern int M[MEM_SIZE];
extern int SP;
extern int FP;
extern int HP;
extern float tmp_float;
extern char tmp_string[MAX_STR_LEN];

void putInteger(int);
void putBool(int);
void putString(int x);
void putFloat(float x);

int getInteger();
int getBool();
float getFloat();
void getString();

#endif
