# Карта ISA (full)

Источники: [opcodes.yaml](../isa/opcodes.yaml) (51 мнемоника + NOP/HALT), [spec.md](../isa/spec.md).

Python full: все мнемоники из YAML легальны (`VARIANT_ILLEGAL_OPCODES["full"]` пуст).

## Форматы инструкций


| format        | Поля (биты)                 | Мнемоники                                                                                              |
| ------------- | --------------------------- | ------------------------------------------------------------------------------------------------------ |
| `bare`        | —                           | EI, DI, IRET                                                                                           |
| `rrr`         | r1, r2, res                 | ADD, SUB, AND, OR, XOR, ADDS, SUBS, BIC, MVN, NEG, SLL, SLR, SAL, ROL, ROR, ADC, ADCS, SBC, SBCS, ANDS |
| `imm16`       | r1, immh, res, imm11        | ADDI, SUBI, ADDSI, SUBSI                                                                               |
| `load_store`  | raddr, r1/dest, imm11, mask | LDR, LDRPRE, LDRPOST, LDREX                                                                            |
| `store`       | raddr, r1/src, imm11, mask  | STR, STRPRE, STRPOST                                                                                   |
| `strex`       | raddr, r1, rstatus, imm11   | STREX                                                                                                  |
| `mul`         | r1, r2, res                 | SMUL, MUL                                                                                              |
| `mul64`       | r1, r2, res, resh           | UMULL, SMULL                                                                                           |
| `mla`         | r1, r2, res                 | MLA                                                                                                    |
| `branch`      | r1, imm11                   | JMP, JZ, JNZ, JC, JS, JO                                                                               |
| `branch_cond` | cond, r1, imm11             | BJ                                                                                                     |
| `spr`         | r1, spr                     | READSPR, WRITESPR                                                                                      |


## Группы по функции

### Память — загрузка


| Mnemonic | Действие                                           |
| -------- | -------------------------------------------------- |
| LDR      | `EA = R[raddr]+imm`; load с маской в R[dest@20:16] |
| LDRPRE   | `R[raddr] += imm`; load по новому базовому         |
| LDRPOST  | load; затем `R[raddr] += imm`                      |
| LDREX    | установить exclusive monitor + load                |


### Память — сохранение


| Mnemonic         | Действие                            |
| ---------------- | ----------------------------------- |
| STR              | store с маской                      |
| STRPRE / STRPOST | аналогично pre/post index           |
| STREX            | условный store + status в `rstatus` |


### Умножение


| Mnemonic      | Результат                                                                       |
| ------------- | ------------------------------------------------------------------------------- |
| SMUL          | signed 32×32 → low 32 в `res`                                                   |
| MUL           | unsigned 64; low→`res`, high→`resh` [10:6]                                      |
| UMULL / SMULL | то же для unsigned / signed 64-bit product                                      |
| MLA           | `res ← (R[r1]*R[r2])[31:0] + R[res_field]` — аккумулятор в поле **res** [15:11] |


### Арифметика/логика (без флагов)

ADD, SUB, AND, OR, XOR, BIC, MVN, NEG, SLL, SLR, SAL, ROL, ROR, ADDI, SUBI, ADC, SBC.

### Арифметика с флагами

ADDS, SUBS, ADCS, SBCS, ANDS, ADDSI, SUBSI — обновляют Z, C, V, S по правилам spec.

### Переходы


| Mnemonic     | Условие                         |
| ------------ | ------------------------------- |
| JMP          | безусловно `PC = R[r1] + imm11` |
| JZ / JNZ     | Zero / not Zero                 |
| JC / JS / JO | Carry / Sign / Overflow         |
| BJ           | ARM-стиль: cond 0–14 в [25:22]  |


### Системные


| Mnemonic           | Эффект           |
| ------------------ | ---------------- |
| NOP                | нет              |
| HALT               | останов          |
| EI / DI            | Intenable on/off |
| READSPR / WRITESPR | доступ к SPR     |
| IRET               | return from IRQ  |


## Псевдо-операции (ассемблер)

Не отдельные opcodes; разворачиваются в `core/asm.py`:


| Pseudo     | Expansion                          |
| ---------- | ---------------------------------- |
| CMP r1, r2 | SUBS r1, r2, 0                     |
| CMN r1, r2 | ADDS r1, r2, 0                     |
| TST / TEST | ANDS r1, r2, 0                     |
| MOV / MOVI | ADDI 0, dst, imm                   |
| PUSH / POP | SUBI/STRPOST и LDRPOST/ADDI на R30 |


## Кодировка: примеры

```
ADDS r1, r2, r3:
  opcode=35 << 26 | r1<<21 | r2<<16 | r3<<11

READSPR r5, 3:
  opcode=52 << 26 | r5<<21 | 3<<11

LDR r2, r10, imm, mask:
  opcode=1 << 26 | fields per load_store format
```

Полная таблица: `python -c` или дизассемблер `core.disasm`.

## Что входит в full и исключено в tn9k

TN9K illegal (RTL + Python variant): SMUL, MUL, UMULL, SMULL, MLA, LDREX, STREX, LDRPRE/POST, STRPRE/POST, JS, JO — см. [06-parity-matrix.md](06-parity-matrix.md).