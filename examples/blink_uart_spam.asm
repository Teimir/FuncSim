# UART smoke test: BL\n in a tight loop (no delay). Use if blink_uart is silent.

MOV 21 -1
MOV 22 16
SLL 21 22 21
ADDI 21 23 4096
MOV 10 66
MOV 11 76
MOV 19 10
MOV 15 28

# loop @ 28:
STR 23 10 1 0
STR 23 11 1 0
STR 23 19 1 0
JMP 15 0
