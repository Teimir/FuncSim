# 05 — Умножение

Lab: [asm/lab_mul.asm](asm/lab_mul.asm) — `6*7=42` в `r3`.

## Форматы


| Мнемоника | Синтаксис              | Результат                                      |
| --------- | ---------------------- | ---------------------------------------------- |
| **MUL**   | `MUL r1 r2 res resh`   | 64-bit `u32(r1)*u32(r2)` → `res`=lo, `resh`=hi |
| **UMULL** | `UMULL r1 r2 res resh` | То же беззнаковое                              |
| **SMULL** | `SMULL r1 r2 res resh` | Знаковое 32×32→64                              |
| **SMUL**  | `SMUL r1 r2 res`       | Только младшие 32 бита знакового произведения  |
| **MLA**   | `MLA r1 r2 racc res`   | `res = low32(u32(r1)*u32(r2)+u32(racc))`       |


Пример MUL:

```asm
MOV 1 6
MOV 2 7
MUL 1 2 3 0
HALT
```

## Профили ядра


| Профиль                | MUL / UMULL / LDREX                             |
| ---------------------- | ----------------------------------------------- |
| Python `full`          | Да                                              |
| RTL `core_tn9k` / FPGA | **Illegal** — см. [profiles.md](../profiles.md) |


Проверка FEATURES: `READSPR r 5` — битовая маска возможностей.

## Запуск

```bash
python -m cli.sim --asm docs/tutorial/asm/lab_mul.asm --until-halt --dump-regs
```

