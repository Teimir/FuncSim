# TN9K bring-up: one byte 0x55 ('U') then halt loop. No LF (0x0A).
MOV 21 -1
MOV 22 16
SLL 21 22 21
ADDI 21 23 4096

MOV 10 85
STR 23 10 1 0

idle:
NOP
B idle
