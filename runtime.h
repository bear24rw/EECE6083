#ifndef __RUNTIME_H__
#define __RUNTIME_H__

#include <stdio.h>

#define NUM_REGS  100
#define MEM_SIZE  100

extern int R[NUM_REGS];
extern int M[MEM_SIZE];
extern int SP;
extern int FP;

void putInteger(int);
void putBool(int);

#endif
