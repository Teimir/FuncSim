# 09 — Ядро Python (`src/core/`)

Обзор: [architecture.md](../architecture.md). Full-core эталон: [core-full/README.md](../core-full/README.md).

## Цикл исполнения

```mermaid
flowchart LR
  fetch[fetch word at PC] --> decode[decode_word]
  decode --> exec[execute]
  exec --> inc[PC plus 4 unless branch]
  inc --> bus[on_step_end MMIO]
```

| Модуль | Файл | Роль |
|--------|------|------|
| Состояние | `state.py` | 32 GPR, flags, SPR, halted, exclusive |
| Декод | `decode.py` | YAML opcodes → `DecodedInsn` |
| Исполнение | `execute.py` | Семантика каждой мнемоники |
| Цикл | `runner.py` | step(), breakpoints, cycles |
| RAM | `memory.py` | Массив слов |
| Шина | `bus.py` | RAM + MMIO decode |
| Отладка | `debug_controller.py` | Обёртка для GUI/GDB |

## CPUState

- `reg_read(i)` — r0 всегда 0.
- `pc` — alias `r31`.
- `flags` — Intenable, Z, C, V, S.
- `spr[]` — SAVED_IRQ_PC, IRQ_VECTOR, IRQ_MASK, …

## Runner

```python
from core.state import CPUState
from core.memory import Memory
from core.runner import Runner

st = CPUState()
mem = Memory()
r = Runner(st, mem)
while not st.halted:
    r.step()
```

После шага с MMIO: `SystemBus.on_step_end` обновляет timer и может вызвать `raise_irq`.

## Циклы инструкций

`core/cycles.py` — большинство инструкций = 1; MUL = 3; LDR/STR = 2. Счётчик: `runner.cycle_counter`.

## Тест ISA

Векторы: `tests/isa/test_vectors.yaml`. Запуск:

```bash
pytest tests/isa/ -q
```

Добавление вектора: одна запись yaml + ожидаемые регистры/флаги после `Runner.step()`.

## MMIO codegen

После правок [mmio_map.yaml](../isa/mmio_map.yaml):

```bash
python scripts/gen_mmio.py
```

## Дальше

[10-peripherals-mmio.md](10-peripherals-mmio.md)
