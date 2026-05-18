# 07 — Системные инструкции, SPR, IRQ

Lab: [asm/lab_system.asm](asm/lab_system.asm) — `READSPR 2 3` (CORE_INFO).

## EI / DI / IRET


| Мнемоника | Эффект                                         |
| --------- | ---------------------------------------------- |
| **EI**    | Intenable ← 1                                  |
| **DI**    | Intenable ← 0                                  |
| **IRET**  | PC ← SPR[SAVED_IRQ_PC]; сброс `irq_in_service` |


## SPR


| Мнемоника    | Синтаксис              |
| ------------ | ---------------------- |
| **READSPR**  | `READSPR r spr_index`  |
| **WRITESPR** | `WRITESPR r spr_index` |



| Индекс | Имя          | Доступ                                |
| ------ | ------------ | ------------------------------------- |
| 0      | SAVED_IRQ_PC | R/W                                   |
| 1      | IRQ_VECTOR   | R/W                                   |
| 2      | IRQ_MASK     | R/W (бит i=1 → линия i замаскирована) |
| 3      | CORE_INFO    | RO                                    |
| 4      | ISA_REVISION | RO                                    |
| 5      | FEATURES     | RO                                    |


Практика IRQ + timer: [15-irq-timer-lab.md](15-irq-timer-lab.md).

---

## Матрица всех 51 мнемоник

Источник: [opcodes.yaml](../isa/opcodes.yaml).


| Мнемоника | Opcode [31:26] | Формат       | Глава | Lab              |
| --------- | -------------- | ------------ | ----- | ---------------- |
| NOP       | 0b000000       | special_nop  | 01    | lab_fundamentals |
| LDR       | 0b000001       | load_store   | 04    | lab_mem          |
| STR       | 0b000010       | store        | 04    | lab_mem          |
| ROL       | 0b000011       | rrr          | 02    | lab_alu          |
| SMUL      | 0b000100       | rrr          | 02/05 | lab_mul          |
| JMP       | 0b010000       | branch       | 06    | lab_branch       |
| JZ        | 0b010001       | branch       | 06    | lab_branch       |
| JNZ       | 0b010010       | branch       | 06    | lab_branch       |
| JC        | 0b010011       | branch       | 06    | lab_branch       |
| JS        | 0b010100       | branch       | 06    | lab_branch       |
| JO        | 0b010101       | branch       | 06    | lab_branch       |
| LDRPOST   | 0b010110       | load_store   | 04    | 08 PUSH/POP      |
| LDRPRE    | 0b000101       | load_store   | 04    | —                |
| STRPRE    | 0b000110       | store        | 04    | —                |
| LDREX     | 0b000111       | load_store   | 04    | —                |
| STREX     | 0b100000       | strex        | 04    | —                |
| STRPOST   | 0b010111       | store        | 04    | 08 PUSH/POP      |
| UMULL     | 0b001000       | mul          | 05    | —                |
| SMULL     | 0b001001       | mul          | 05    | —                |
| MLA       | 0b001010       | mla          | 05    | —                |
| BIC       | 0b001011       | rrr          | 02    | —                |
| MVN       | 0b001100       | rrr          | 02    | —                |
| NEG       | 0b001101       | rrr          | 02    | —                |
| ANDS      | 0b001110       | rrr          | 02    | —                |
| ROR       | 0b001111       | rrr          | 02    | lab_alu          |
| ADD       | 0b100001       | rrr          | 02    | lab_alu          |
| SUB       | 0b100010       | rrr          | 02    | —                |
| ADDS      | 0b100011       | rrr          | 02    | lab_alu          |
| SUBS      | 0b100100       | rrr          | 02    | lab_alu          |
| AND       | 0b100101       | rrr          | 02    | lab_alu          |
| OR        | 0b100110       | rrr          | 02    | lab_alu          |
| XOR       | 0b100111       | rrr          | 02    | lab_alu          |
| SLL       | 0b101000       | rrr          | 02    | lab_alu          |
| SLR       | 0b101001       | rrr          | 02    | —                |
| SAL       | 0b101010       | rrr          | 02    | —                |
| MUL       | 0b101100       | mul          | 05    | lab_mul          |
| ADDI      | 0b110000       | imm16        | 03    | lab_imm          |
| SUBI      | 0b110001       | imm16        | 03    | lab_imm          |
| BJ        | 0b011000       | branch_cond  | 06    | lab_branch       |
| WRITESPR  | 0b011001       | spr          | 07    | —                |
| ADDSI     | 0b011010       | imm16        | 03    | lab_imm          |
| SUBSI     | 0b011011       | imm16        | 03    | —                |
| ADC       | 0b011100       | rrr          | 02    | —                |
| ADCS      | 0b011101       | rrr          | 02    | —                |
| SBC       | 0b011110       | rrr          | 02    | —                |
| SBCS      | 0b011111       | rrr          | 02    | —                |
| EI        | 0b110010       | bare         | 07    | 15               |
| DI        | 0b110011       | bare         | 07    | 15               |
| READSPR   | 0b110100       | spr          | 07    | lab_system       |
| IRET      | 0b111110       | bare         | 07    | 15               |
| HALT      | 0b111111       | special_halt | 01    | все labs         |


Псевдоинструкции (не отдельные опкоды): CMP, CMN, TST, MOV, MOVI, PUSH, POP, BEQ…BAL, B — [08-assembler-and-images.md](08-assembler-and-images.md).