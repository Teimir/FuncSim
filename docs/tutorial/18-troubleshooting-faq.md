# 18 — Troubleshooting / FAQ

## `ModuleNotFoundError: yaml` / `hypothesis`

```bash
pip install -e ".[dev]"
```

## `pytest` слишком долгий

```bash
pytest -q -m "not slow"
```

## `assemble error` / `unknown mnemonic`

- Одна инструкция на строку.
- Имена мнемоник как в [opcodes.yaml](../isa/opcodes.yaml).
- Ветки: `BEQ label` или `BEQ 31 imm` в пределах ±1023 **слов**.

## `MisalignedAccess`

`LDR`/`STR` только при `addr % 4 == 0`.

## MMIO не работает

Нужен `--mmio` или `--sd-image`. Адреса от `0xFFFF0000` (default).

## UART «молчит» в GUI

- Включите `--mmio`.
- Для калькулятора: строка с `\n`, команда `HALT\n`.
- **Ctrl+U** — отдельное окно terminal.

## Timer IRQ не срабатывает

1. `EI` выполнен?
2. `WRITESPR` vector = адрес handler?
3. `PERIOD` и `IRQ_EN` в CTRL?
4. `IRQ_MASK` не блокирует линию 0?

См. [15-irq-timer-lab.md](15-irq-timer-lab.md).

## GDB `Connection refused`

1. Stub запущен: `python -m cli.gdb_server --hex …`
2. Порт 3333 свободен.
3. `target remote 127.0.0.1:3333`

## SD `NO_MEDIUM` / mount

GUI **Storage** → Browse → Mount, или `--sd-image` при старте.

## README timer vs mmio.md

Актуальная модель: **32-bit COUNTER + PERIOD**, не 64-bit LO/HI. Канон: [mmio.md](../mmio.md).

## RTL / iverilog не найден

Опционально для [16-rtl-cosim-fpga.md](16-rtl-cosim-fpga.md). Python-туториалы работают без Verilog.

## Где спросить дальше

- [BACKLOG.md](../BACKLOG.md) — известные ограничения
- Issues репозитория

