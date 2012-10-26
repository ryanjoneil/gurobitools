set rows := {1 .. 5};
set cols := {1 .. 3};

param b[cols] := <1> 15, <2> 15, <3> 15;

param c[rows * cols] :=
        |  1,  2,  3 |
    | 1 |  6, 10,  1 |
    | 2 | 12, 12,  5 |
    | 3 | 15,  4,  3 |
    | 4 | 10,  3,  9 |
    | 5 |  8,  9,  5 |;

param a[rows * cols] :=
        |  1,  2,  3 |
    | 1 |  5,  7,  2 |
    | 2 | 14,  8,  7 |
    | 3 | 10,  6, 12 |
    | 4 |  8,  4, 15 |
    | 5 |  6, 12,  5 |;

var x[rows * cols] binary;

maximize z: sum <i,j> in rows * cols: c[i,j] * x[i,j];

subto c1:
    forall <i> in rows:
        sum <j> in cols: x[i,j] <= 1;

subto c2:
    forall <j> in cols:
        sum <i> in rows: a[i,j] * x[i,j] <= b[j];
