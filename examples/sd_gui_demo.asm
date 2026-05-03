# SD card MMIO demo for the debugger GUI.
# Pool at 0x100: word0 = SD MMIO base (0xFFFF3000), word1 = magic (0xDEADC0DE).
# Main at 0x200: write magic to sector 0, read back, compare; GPIO out = 1 if OK, 2 if mismatch.
#
# Note: R31 is the program counter; never use it as a general-purpose register.

ADDI 0 20 256
LDR 20 22 15 0
SUBI 22 21 12288
LDR 20 3 15 4
STR 22 3 15 16
ADDI 0 4 0
STR 22 4 15 8
ADDI 0 5 2
STR 22 5 15 0
ADDI 0 6 0
STR 22 6 15 16
ADDI 0 7 1
STR 22 7 15 0
LDR 22 8 15 16
SUBS 3 8 9
ADDI 0 29 512
JZ 29 80
ADDI 0 30 2
STR 21 30 15 0
HALT
ADDI 0 30 1
STR 21 30 15 0
HALT
