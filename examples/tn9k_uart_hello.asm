# TN9K: "Hi!\r\n" @ 115200. UART base in r23; payload only in r1 (low reg, no NOP padding).

MOV 21 -1
MOV 22 16
SLL 21 22 21
ADDI 21 23 4096

MOV 1 72
STR 23 1 1 0
MOV 1 105
STR 23 1 1 0
MOV 1 33
STR 23 1 1 0
MOV 1 13
STR 23 1 1 0
MOV 1 10
STR 23 1 1 0

HALT
