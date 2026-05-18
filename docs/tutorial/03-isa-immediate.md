# 03 — Немедленные операнды

Формат **imm16:** `MNEMONIC r1 res imm16` — 16-битное значение знаково расширяется до 32 бит.

Lab: [asm/lab_imm.asm](asm/lab_imm.asm)

## ADDI / SUBI


| Мнемоника | Синтаксис           | Семантика                     |
| --------- | ------------------- | ----------------------------- |
| **ADDI**  | `ADDI r1 res imm16` | `res = u32(r1) + sext(imm16)` |
| **SUBI**  | `SUBI r1 res imm16` | `res = u32(r1) - sext(imm16)` |


```asm
ADDI 0 1 100
SUBI 1 3 5
```

## ADDSI / SUBSI

Как ADDI/SUBI, но с обновлением флагов Z,C,V,S (как ADDS/SUBS).


| Мнемоника | Синтаксис            |
| --------- | -------------------- |
| **ADDSI** | `ADDSI r1 res imm16` |
| **SUBSI** | `SUBSI r1 res imm16` |


## Псевдо MOV / MOVI


| Псевдо         | Развёртка        |
| -------------- | ---------------- |
| `MOV dst imm`  | `ADDI 0 dst imm` |
| `MOVI dst imm` | то же            |


```asm
MOV 5 0x1234
```

## Запуск

```bash
python -m cli.sim --asm docs/tutorial/asm/lab_imm.asm --until-halt --dump-regs
```

Ожидание: `r3=100`, `r4=95`.