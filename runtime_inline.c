putinteger:
    SP++;
    R[0] = M[SP];
    putInteger(R[0]);
    SP++;
    R[0] = M[SP];
    goto *(void *)R[0];

putbool:
    SP++;
    R[0] = M[SP];
    putBool(R[0]);
    SP++;
    R[0] = M[SP];
    goto *(void *)R[0];
