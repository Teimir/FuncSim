# Идентификация ядра E32C (SPR)

Источник истины: `[cores.yaml](cores.yaml)`. Регенерация: `python scripts/gen_cores.py`.

ПО читает версию через **READSPR** (вариант A — без MMIO):

```asm
READSPR r1, 3    ; CORE_INFO  — ожидаем 0xE32Cvv00 (vv = variant)
READSPR r1, 4    ; ISA_REVISION
READSPR r1, 5    ; FEATURES
```


| Variant | CORE_INFO    | FEATURES     |
| ------- | ------------ | ------------ |
| full    | `0xE32C0100` | `0x0000000B` |
| tn9k    | `0xE32C0110` | `0x0000000A` |
| lite    | `0xE32C0120` | `0x00000000` |


Проверка возможности без имени варианта: `READSPR` + тест бита в FEATURES (бит 0 = MUL).

Константы Python: `core.spr_constants`. RTL: ``include "cores_generated.svh"`.