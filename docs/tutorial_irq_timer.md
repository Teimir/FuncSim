# Tutorial: IRQ и timer в симуляторе (без RTL)

Пошаговый сценарий только для **Python** (`cli.sim` / GUI / GDB). Плата и `test/` не нужны.

## Идея

1. Включить прерывания (`EI`).
2. Настроить timer: compare = N циклов, `IRQ_EN` в CTRL.
3. В обработчике (адрес из `SPR[IRQ_VECTOR]`) — минимальная работа, например запись в UART.
4. Вернуться: `READSPR` saved PC → `JMP`.

## MMIO (база `0xFFFF_0000`)

| Устройство | Смещение |
|----------|----------|
| Timer CTRL | `0xFFFF_2010` |
| Timer COMPARE_LO | `0xFFFF_2008` |
| UART TX | `0xFFFF_1000` |

См. [mmio.md](mmio.md) — счётчик 64-bit читается как **COMPARE_LO/HI** и **COUNTER_LO/HI** (два слова).

## Пример asm

Готовые исходники: `examples/blink_uart_irq_main.asm` (main) и `examples/blink_uart_irq_handler.asm` (handler @ `0x100`).

Сборка в hex (из корня репо):

```bash
python -m cli.asm examples/blink_uart_irq_main.asm -o /tmp/main.hex
```

Или использовать прошивочный скрипт для FPGA (только чтение): `scripts/gen_firmware_hex.py` — см. [test/fpga/README.md](../test/fpga/README.md).

## Запуск в симуляторе

```bash
python -m cli.sim --mmio --asm examples/blink_uart_irq_main.asm --max-steps 500000 --uart-stdout
```

GUI:

```bash
e32c-debug-gui --mmio --hex path/to/image.hex
```

Установите **IRQ vector** (SPR 1) = `0x100` перед run, если загружаете только main без автоматической инициализации SPR — в полном образе прошивки это делает reset/boot код.

## Отладка

- GUI: вкладка MMIO — timer counter, UART TX buffer.
- GDB: `python -m cli.gdb_server --hex … --mmio`, `break *0x100` на handler.

## Дальше

- [examples/README.md](../examples/README.md) — все демо
- [tutorial и HAL](../examples/lib/) — после `examples/lib/mmio.inc`
