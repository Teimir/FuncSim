# Timer IRQ ~1 Hz @ 27 MHz. Handler must be linked at 0x100 (see gen_firmware_hex.py).
# MMIO: r22=UART 0xFFFF1000, r24=timer 0xFFFF2000 (period default 27M in RTL).

DI
MOV 21 -1
MOV 22 16
SLL 21 22 21
ADDI 21 22 4096
ADDI 21 24 8192

ADDI 0 21 256
WRITESPR 21 1

ADDI 0 20 1
STR 24 20 15 16

EI
idle:
NOP
B idle
