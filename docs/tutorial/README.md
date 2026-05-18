# Туториалы E32C

Пошаговые руководства по всем частям репозитория: ISA (все 51 мнемоника), ядро Python, MMIO, CLI, GUI, GDB, RTL/FPGA.

**Канон семантики:** [isa/spec.md](../isa/spec.md) · **MMIO:** [mmio.md](../mmio.md) · **Контракт Python↔RTL:** [wrapper_interface.md](../wrapper_interface.md)

---

## Оглавление

| № | Документ | Тема |
|---|----------|------|
| 00 | [00-setup-and-repo.md](00-setup-and-repo.md) | Установка, pytest, карта репозитория |
| 01 | [01-isa-fundamentals.md](01-isa-fundamentals.md) | Слова, регистры, флаги, NOP/HALT |
| 02 | [02-isa-alu-rr.md](02-isa-alu-rr.md) | АЛУ rrr: ADD…XOR, сдвиги, ADC/SBC, BIC/MVN/NEG |
| 03 | [03-isa-immediate.md](03-isa-immediate.md) | ADDI/SUBI, ADDSI/SUBSI |
| 04 | [04-isa-memory.md](04-isa-memory.md) | LDR/STR, pre/post, LDREX/STREX |
| 05 | [05-isa-multiply.md](05-isa-multiply.md) | MUL, UMULL, SMULL, SMUL, MLA |
| 06 | [06-isa-branches.md](06-isa-branches.md) | JMP, JZ…JO, BJ/BEQ…, псевдо CMP |
| 07 | [07-isa-system-spr-irq.md](07-isa-system-spr-irq.md) | SPR, EI/DI, IRET + **матрица 51×1** |
| 08 | [08-assembler-and-images.md](08-assembler-and-images.md) | cli.asm, hex/bin, PUSH/POP |
| 09 | [09-core-python.md](09-core-python.md) | Архитектура `src/core/` |
| 10 | [10-peripherals-mmio.md](10-peripherals-mmio.md) | GPIO, UART, Timer, SD |
| 11 | [11-cli-simulator.md](11-cli-simulator.md) | `python -m cli.sim` |
| 12 | [12-cli-debug-repl.md](12-cli-debug-repl.md) | `python -m cli.debug` |
| 13 | [13-cli-debug-gui.md](13-cli-debug-gui.md) | `e32c-debug-gui` |
| 14 | [14-gdb-remote.md](14-gdb-remote.md) | GDB Remote stub |
| 15 | [15-irq-timer-lab.md](15-irq-timer-lab.md) | Timer IRQ + UART handler |
| 16 | [16-rtl-cosim-fpga.md](16-rtl-cosim-fpga.md) | RTL, cosim, Tang Nano 9K |
| 17 | [17-examples-walkthrough.md](17-examples-walkthrough.md) | Каталог `examples/` |
| 18 | [18-troubleshooting-faq.md](18-troubleshooting-faq.md) | Частые проблемы |

Лабораторные `.asm`: каталог [asm/](asm/).

---

## Треки обучения

### Beginner (симулятор без RTL)

1. 00 → 01 → 08 → 11  
2. `python examples/launch_smoke.py`  
3. 10 (GPIO/UART) → 13 (GUI)

### Developer (ISA + отладка)

1. 02 → 03 → 04 → 05 → 06 → 07 (все labs в `asm/`)  
2. 09 → 12 → 14  
3. 15 (IRQ)

### RTL / FPGA

1. Треки Beginner + Developer (минимум 01, 10)  
2. 16 + [test/README.md](../../test/README.md) + [test/fpga/README.md](../../test/fpga/README.md)

---

## Чеклист «прошёл всё»

- [ ] Собрал и запустил `pytest -q -m "not slow"`
- [ ] Прогнал все `docs/tutorial/asm/*.asm` через `cli.sim`
- [ ] Открыл GUI, сделал Step/Run N, UART terminal
- [ ] Подключил GDB (`launch_gdb_smoke.py`)
- [ ] Прочитал матрицу 51 мнемоники в [07](07-isa-system-spr-irq.md)
- [ ] (Опционально) `verify_all.py` или smoke RTL из главы 16

---

## Быстрый запуск lab

Из корня репозитория (после `pip install -e ".[dev]"`):

```bash
python -m cli.sim --asm docs/tutorial/asm/lab_alu.asm --until-halt --dump-regs
```

Windows PowerShell — те же команды; путь с пробелами в кавычках.
