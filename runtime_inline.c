putinteger:
    R[0] = M[FP];
    putInteger(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    /* cleaning up argument stack */
    SP = SP - 1;
    /* cleaning up return addr and old FP */
    SP = SP - 2;
    goto *(void *)R[0];

putbool:
    R[0] = M[FP];
    putBool(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    /* cleaning up argument stack */
    SP = SP - 1;
    /* cleaning up return addr and old FP */
    SP = SP - 2;
    goto *(void *)R[0];
