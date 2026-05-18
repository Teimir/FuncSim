# 15 — Lab: Timer IRQ и UART

Пошаговый сценарий **только Python** (без RTL).

## Идея

1. `EI` — разрешить прерывания.
2. Записать `IRQ_VECTOR` (SPR 1) = адрес handler.
3. Timer: `PERIOD`, `CTRL.IRQ_EN`.
4. В handler — работа (UART), `IRET`.

## MMIO (база `0xFFFF_0000`)


| Устройство      | Адрес         |
| --------------- | ------------- |
| UART TX         | `0xFFFF_1000` |
| Timer PERIOD_LO | `0xFFFF_2008` |
| Timer CTRL      | `0xFFFF_2010` |


См. [mmio.md](../mmio.md), [wrapper_interface.md](../wrapper_interface.md).

## Исходники


| Файл                                  | Роль              |
| ------------------------------------- | ----------------- |
| `examples/blink_uart_irq_main.asm`    | main              |
| `examples/blink_uart_irq_handler.asm` | handler @ `0x100` |


Сборка:

```bash
python -m cli.asm examples/blink_uart_irq_main.asm -o /tmp/irq_main.hex
```

## Симулятор

```bash
python -m cli.sim --mmio --asm examples/blink_uart_irq_main.asm --max-steps 500000 --uart-stdout
```

Убедитесь, что **IRQ_VECTOR** указывает на handler (в полном образе — init-код; иначе задайте SPR в GUI/GDB до run).

## GUI

```bash
e32c-debug-gui --mmio --asm examples/blink_uart_irq_main.asm
```

- Вкладка **MMIO** — counter, PENDING, UART TX.
- **Ctrl+U** — UART terminal.

## GDB

```bash
python -m cli.gdb_server --mmio --asm examples/blink_uart_irq_main.asm
```

В GDB: `break *0x100` на handler.

## FPGA (только чтение)

`scripts/gen_firmware_hex.py` — [test/fpga/README.md](../../test/fpga/README.md).

## Дальше

[16-rtl-cosim-fpga.md](16-rtl-cosim-fpga.md)