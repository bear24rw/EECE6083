putinteger:
    R[0] = M[FP];
    putInteger(R[0]);
    R[0] = M[FP-2];
    goto *(void *)R[0];

putbool:
    R[0] = M[FP];
    putBool(R[0]);
    R[0] = M[FP-2];
    goto *(void *)R[0];
