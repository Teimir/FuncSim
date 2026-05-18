# Lab 06: BEQ after CMP — r4=1 when r1==r2
MOV 1 5
MOV 2 5
CMP 1 2
BEQ equal
MOV 4 0
B done
equal:
MOV 4 1
done:
HALT
