# Boot RAM smoke test: GPIO mask 0x0F, UART 'K', idle loop.
# MMIO: r2 = GPIO 0xFFFF0000, r3 = UART 0xFFFF1000

MOV 2 -1
MOV 4 16
SLL 2 4 2

MOV 1 15
STR 2 1 15 0

MOV 3 -1
MOV 4 16
SLL 3 4 3
ADDI 3 3 4096

MOV 4 75
STR 3 4 1 0

idle:
NOP
B idle
