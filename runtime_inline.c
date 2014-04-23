putinteger:
    R[0] = M[FP];
    putInteger(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];

putbool:
    R[0] = M[FP];
    putBool(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];

putstring:
    R[0] = M[FP];
    putString(R[0]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];
