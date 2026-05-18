# 04 — Память: LDR, STR и расширения

## LDR / STR


| Мнемоника | Синтаксис                    | Поля                      |
| --------- | ---------------------------- | ------------------------- |
| **LDR**   | `LDR raddr rdest mask imm11` | EA = R[raddr]+sext(imm11) |
| **STR**   | `STR raddr rdata mask imm11` | Запись байтов по mask     |


**mask** — 5 бит: бит `k` включает байт `k` слова (0 = LSB).

- **LDR:** выбранные байты из памяти → в `rdest`; сброшенные биты mask → 0 в результате.
- **STR:** RMW: читается слово, подставляются байты из `rdata`, записывается обратно.
- `mask=0`: LDR → 0; STR — no-op для памяти.

Пример (младший байт):

```asm
MOV 1 0x100
MOV 2 0xAA
STR 1 2 1 0
LDR 1 5 1 0
```

Lab: [asm/lab_mem.asm](asm/lab_mem.asm) → `r5=0x000000AA`.

## Pre-index


| Мнемоника  | Порядок                      |
| ---------- | ---------------------------- |
| **LDRPRE** | `R[raddr]+=imm`, затем load  |
| **STRPRE** | `R[raddr]+=imm`, затем store |


## Post-index


| Мнемоника   | Порядок                      |
| ----------- | ---------------------------- |
| **LDRPOST** | load, затем `R[raddr]+=imm`  |
| **STRPOST** | store, затем `R[raddr]+=imm` |


Используются в псевдо **PUSH**/**POP** на `r30` — см. [08-assembler-and-images.md](08-assembler-and-images.md).

## Эксклюзивный доступ


| Мнемоника | Синтаксис                                                            |
| --------- | -------------------------------------------------------------------- |
| **LDREX** | `LDREX raddr rdest mask imm11` — захват монитора                     |
| **STREX** | `STREX raddr rsrc rstatus imm11` — `rstatus=0` при успехе, иначе `1` |


На **TN9K** / `core_tn9k` — illegal; в Python-симуляторе — упрощённая модель `exclusive_`* в `CPUState`.

## Проверка

```bash
python -m cli.sim --asm docs/tutorial/asm/lab_mem.asm --until-halt --dump-regs
```

**Важно:** для MMIO используйте адреса из [mmio.md](../mmio.md) только с включённым `--mmio` — иначе обращение идёт в RAM.