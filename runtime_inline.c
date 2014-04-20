putinteger:
    R[0] = M[FP-1];
    putInteger(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    goto *(void *)R[0];

putbool:
    R[0] = M[FP];
    putBool(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    goto *(void *)R[0];
