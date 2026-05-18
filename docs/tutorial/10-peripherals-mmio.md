# 10 — Периферия и MMIO

Карта: [mmio.md](../mmio.md). Контракт Python↔RTL: [wrapper_interface.md](../wrapper_interface.md).

База по умолчанию: **`0xFFFF_0000`**, окно **`0x4000`**.

| Смещение | Устройство | Python |
|----------|----------|--------|
| +0x0000 | GPIO OUT | `peripherals/gpio.py` |
| +0x1000 | UART | `peripherals/uart.py` |
| +0x2000 | Timer | `peripherals/timer.py` |
| +0x3000 | SD block / SPI | `sd_card.py` / `sd_spi.py` |

Включение в CLI: `--mmio` или `--sd-image` (автоматически создаёт `SystemBus`).

## GPIO (+0x0000)

| +off | Регистр | Доступ |
|------|---------|--------|
| 0x00 | OUT | R/W 32-bit latch |

```bash
python examples/device_demo.py
python examples/device_demo_gui.py
```

## UART (+0x1000)

| +off | Имя | Доступ |
|------|-----|--------|
| 0x00 | TXDATA | W |
| 0x04 | RXDATA | R |
| 0x08 | STATUS | R — RX_READY(0), TX_IDLE(1), TX_FULL(2), RX_FULL(3) |
| 0x0C | CTRL | R/W — IRQ_RX(0), IRQ_TX(1) |

FIFO depth: **8**. Симулятор:

```bash
python -m cli.sim --mmio --asm examples/boot_smoke.asm --uart-stdout
python examples/uart_calculator.py
```

В GUI: **Ctrl+U** — UART terminal; для REPL-калькулятора отправляйте `HALT\n`.

## Timer (+0x2000)

32-bit **COUNTER** @+0, **PERIOD_LO/HI** @+8/+0xC, **CTRL** @+0x10 (IRQ_EN, PENDING, ACK W1C).

IRQ при `counter >= period` и разрешённых прерываниях — [15-irq-timer-lab.md](15-irq-timer-lab.md).

## SD block (+0x3000, по умолчанию)

| +off | Имя | Описание |
|------|-----|----------|
| 0x00 | CTRL | W: 1=read, 2=write, 3=flush |
| 0x04 | STATUS | READY, ERROR, NO_MEDIUM |
| 0x08 | LBA | сектор |
| 0x10 | DATA | 512 B буфер |

```bash
python examples/sd_probe.py
python examples/launch_sd_gui_demo.py
```

## SD SPI (`--sd-spi`)

Регистры CMD/ARG/STATUS/… — профиль TN9K. См. `SdSpiRegs` в `mmio_sd_regs.py`.

```bash
python examples/sd_spi_probe.py
python examples/launch_tn9k_demo.py
```

## Генерация констант

```bash
python scripts/gen_mmio.py
```

## Дальше

[11-cli-simulator.md](11-cli-simulator.md) · [13-cli-debug-gui.md](13-cli-debug-gui.md) (вкладка MMIO / Storage)
