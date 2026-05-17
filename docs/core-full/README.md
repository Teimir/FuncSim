# E32C Full Core — архитектура и микроархитектура

Документация для **полного ядра** (`core_variant: full`): семантика как в Python (`src/core/`, `CPUState(core_variant="full")`), целевая RTL-реализация — `[test/src/core.sv](../../test/src/core.sv)`.

Это **не** дублирует [ISA spec](../isa/spec.md) построчно и **не** описывает симулятор целиком ([architecture.md](../architecture.md)). Здесь — контракт «что должен делать full core» и как это устроено в референсе и в RTL.

## Содержание


| Файл                                               | Тема                                                             |
| -------------------------------------------------- | ---------------------------------------------------------------- |
| [01-architecture.md](01-architecture.md)           | Программная архитектура: GPR, PC, флаги, SPR, память, исключения |
| [02-isa-mapping.md](02-isa-mapping.md)             | Карта ISA: форматы, группы опкодов, псевдо-инструкции            |
| [03-microarchitecture.md](03-microarchitecture.md) | Микроархитектура RTL: FSM, интерфейсы, задержки, IRQ             |
| [04-python-reference.md](04-python-reference.md)   | Референсная модель Python: модули и поток исполнения             |
| [05-rtl-full-current.md](05-rtl-full-current.md)   | Текущий `e32c_core`: что реализовано сегодня                     |
| [06-parity-matrix.md](06-parity-matrix.md)         | Матрица соответствия Python ↔ RTL и список разрывов              |


## Связанные документы

- [ISA spec](../isa/spec.md), [opcodes.yaml](../isa/opcodes.yaml)
- [cores.yaml](../isa/cores.yaml), [cores.md](../isa/cores.md) — идентификация варианта (SPR 3–5)
- [profiles.md](../profiles.md) — сравнение full / tn9k / lite
- [test/README.md](../../test/README.md) — RTL и тестбенчи

## Идентификация full core


| SPR            | Значение                            |
| -------------- | ----------------------------------- |
| 3 CORE_INFO    | `0xE32C0100`                        |
| 4 ISA_REVISION | `0x00010005` (ISA 1.5)              |
| 5 FEATURES     | `0x0000000B` (MUL, LDREX, FULL_ISA) |


Константы: `[src/core/spr_constants.py](../../src/core/spr_constants.py)`, `[test/src/cores_generated.svh](../../test/src/cores_generated.svh)`.