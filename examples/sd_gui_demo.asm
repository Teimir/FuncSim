# SD card MMIO demo for the debugger GUI.
# Pool @ 0x100: SD base 0xFFFF3000, magic 0xDEADC0DE. Code @ 0x200.
# ABI (docs/isa/spec.md): R30 = SP, R31 = PC — не использовать их как общие регистры.
# Здесь r9 — временное значение для записи в GPIO.

MOV 20 256
LDR 20 22 15 0
SUBI 22 21 12288
LDR 20 3 15 4
STR 22 3 15 16
MOV 4 0
STR 22 4 15 8
MOV 5 2
STR 22 5 15 0
MOV 6 0
STR 22 6 15 16
MOV 7 1
STR 22 7 15 0
LDR 22 8 15 16
CMP 3 8
MOV 29 512
JZ 29 80
MOV 9 2
STR 21 9 15 0
HALT
MOV 9 1
STR 21 9 15 0
HALT
