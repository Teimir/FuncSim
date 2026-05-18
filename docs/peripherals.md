# MMIO периферия (FuncSim)

**Актуальная карта регистров и единый контракт Python ↔ RTL:** [mmio.md](mmio.md), [wrapper_interface.md](wrapper_interface.md).

Источник истины для генерации констант: [`isa/mmio_map.yaml`](isa/mmio_map.yaml) → `python scripts/gen_mmio.py`.

## Кратко по устройствам

| Устройство | Python | RTL | Примечание |
|----------|--------|-----|------------|
| GPIO | `peripherals/gpio.py` | `test/src/gpio.sv` | 32-bit OUT @ device+0 |
| UART | `peripherals/uart.py` | `test/src/uart.sv` | FIFO 8, STATUS/CTRL как в YAML |
| Timer | `peripherals/timer.py` | `test/src/timer.sv` | 32-bit counter/period, IRQ line |
| SD block | `peripherals/sd_card.py` | `test/src/sd_block.sv` | образ файла на хосте |
| SD SPI | `peripherals/sd_spi.py` | `test/src/sd_spi.sv` | `--sd-spi`, TN9K |

## Стоимость инструкций (циклы)

[`src/core/cycles.py`](../src/core/cycles.py): большинство инструкций — 1 цикл; `MUL` — 3; `LDR`/`STR` — 2.

CLI: `instructions`, `cycles`; при `--cycle-ns` — приблизительные наносекунды.
