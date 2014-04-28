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
    putString(M[FP]);
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];

putfloat:
    memcpy(&tmp_float, &M[FP], sizeof(float));
    putFloat(tmp_float);
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];

getinteger:
getbool:
    R[0] = getInteger();
    M[M[FP]] = R[0];
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];

getfloat:
    tmp_float = getFloat();
    memcpy(&R[0], &tmp_float, sizeof(float));
    M[M[FP]] = R[0];
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];

getstring:
    getString();
    memcpy(&M[HP], tmp_string, MAX_STR_LEN);
    M[M[FP]] = HP;
    HP -= 100;
    R[0] = M[FP-2];
    FP = M[FP-1];
    SP = SP - 3;
    goto *(void *)R[0];
