putinteger:
    R[0] = M[SP];
    SP++;
    putInteger(R[0]);
    R[0] = M[SP];
    SP++;
    goto *(void *)R[0];

putbool:
    R[0] = M[SP];
    SP++;
    putBool(R[0]);
    R[0] = M[SP];
    SP++;
    goto *(void *)R[0];
