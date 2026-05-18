# 06 — Переходы и условия

База: `target = u32(R[raddr]) + sext(imm11)`. После взятого перехода **не** добавляется `+4`.

Lab: [asm/lab_branch.asm](asm/lab_branch.asm)

## Безусловный и по одному флагу


| Мнемоника | Синтаксис                       | Условие |
| --------- | ------------------------------- | ------- |
| **JMP**   | `JMP raddr imm11` или `B label` | всегда  |
| **JZ**    | `JZ raddr imm11` / `JZ label`   | Z       |
| **JNZ**   | `JNZ …`                         | ¬Z      |
| **JC**    | `JC …`                          | C       |
| **JS**    | `JS …`                          | S       |
| **JO**    | `JO …`                          | V       |


Псевдо **B** `label` → `JMP 31 offset` (PC-relative).

## BJ и ARM-условия


| Мнемоника         | Синтаксис               |
| ----------------- | ----------------------- |
| **BJ**            | `BJ cond raddr imm11`   |
| **BEQ** … **BLE** | `BEQ label` → BJ с cond |



| cond | Псевдо  | Условие  |
| ---- | ------- | -------- |
| 0    | BEQ     | Z        |
| 1    | BNE     | ¬Z       |
| 2    | BCS/BHS | C        |
| 3    | BCC/BLO | ¬C       |
| 4    | BMI     | S        |
| 5    | BPL     | ¬S       |
| 6    | BVS     | V        |
| 7    | BVC     | ¬V       |
| 8    | BHI     | C∧¬Z     |
| 9    | BLS     | ¬C∨Z     |
| 10   | BGE     | S=V      |
| 11   | BLT     | S≠V      |
| 12   | BGT     | ¬Z∧(S=V) |
| 13   | BLE     | Z∨(S≠V)  |
| 14   | BAL     | всегда   |
| 15   | BNV     | никогда  |


## Псевдо сравнения


| Псевдо        | Развёртка      |
| ------------- | -------------- |
| **CMP** r1 r2 | `SUBS r1 r2 0` |
| **CMN** r1 r2 | `ADDS r1 r2 0` |
| **TST** r1 r2 | `ANDS r1 r2 0` |


Пример:

```asm
MOV 1 5
MOV 2 5
CMP 1 2
BEQ equal
MOV 4 0
B done
equal:
MOV 4 1
done:
HALT
```

## Запуск

```bash
python -m cli.sim --asm docs/tutorial/asm/lab_branch.asm --until-halt --dump-regs
```

Ожидание: `r4=1`.