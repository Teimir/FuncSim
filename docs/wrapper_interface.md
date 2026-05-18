# Единый контракт обвязки MMIO (Python ↔ RTL)

Документ фиксирует **согласованное представление** периферии между функциональным симулятором и RTL/SoC-тестами.

## Источник истины

| Артефакт | Назначение |
| -------- | ---------- |
| [`isa/mmio_map.yaml`](isa/mmio_map.yaml) | Базы устройств, размеры регионов, таблицы регистров, биты STATUS/CTRL |
| [`scripts/gen_mmio.py`](../scripts/gen_mmio.py) | Генерация заголовков для Python и SystemVerilog |

После правок YAML:

```bash
python scripts/gen_mmio.py
```

## Сгенерированные файлы

### Общая карта (базы)

| Python | RTL (SV) |
| ------ | -------- |
| `src/core/mmio_constants.py` | `test/src/mmio_generated.svh` |

Содержит: `MMIO_BASE_DEFAULT` (`0xFFFF_0000`), `MMIO_WINDOW_SIZE` (`0x4000`), `*_OFFSET`, `*_REGION_SIZE`.

### Регистры устройств

| Устройство | Python | RTL (SV) |
| ---------- | ------ | -------- |
| GPIO | `mmio_gpio_regs.py` → `GpioRegs` | (inline в `gpio.sv`, один регистр OUT @+0) |
| UART | `mmio_uart_regs.py` → `UartRegs` | `uart_regs.svh` (`E32C_UART_OFF_*`, `E32C_UART_STAT_*`) |
| Timer | `mmio_timer_regs.py` → `TimerRegs` | `mmio_timer_regs.svh` + `timer.sv` (word decode) |
| SD block | `mmio_sd_regs.py` → `SdBlockRegs` | `mmio_sd_regs.svh` |
| SD SPI | `mmio_sd_regs.py` → `SdSpiRegs` | `mmio_sd_regs.svh` |

Драйверы Python импортируют константы из сгенерированных модулей:

- `src/core/peripherals/uart.py` ← `UartRegs`
- `src/core/peripherals/timer.py` ← `TimerRegs`
- `src/core/peripherals/sd_card.py` / `sd_spi.py` ← `SdBlockRegs` / `SdSpiRegs`
- `src/core/bus.py` ← `mmio_constants` (маршрутизация по регионам)

## Правила доступа (общие)

1. MMIO — только **32-битные выровненные** слова (`addr % 4 == 0`).
2. База окна по умолчанию: **`0xFFFF_0000`**, размер **`0x4000`**.
3. Смещения в таблицах ниже — **от базы устройства** (не от `MMIO_BASE`), если не указано иное.

## Карта устройств (итог)

| Смещение от MMIO | Устройство | Абсолютная база |
| ---------------- | ---------- | ---------------- |
| `+0x0000` | GPIO | `0xFFFF_0000` |
| `+0x1000` | UART | `0xFFFF_1000` |
| `+0x2000` | Timer | `0xFFFF_2000` |
| `+0x3000` | SD (block или SPI) | `0xFFFF_3000` |

Подробные поля регистров: [mmio.md](mmio.md).

## UART (согласовано)

| +off | Имя | Python `UartRegs` | RTL `E32C_UART_OFF_*` |
| ---- | --- | ----------------- | --------------------- |
| 0x00 | TXDATA | `REG_TXDATA` | `TXDATA` |
| 0x04 | RXDATA | `REG_RXDATA` | `RXDATA` |
| 0x08 | STATUS | `REG_STATUS` | `STATUS` |
| 0x0C | CTRL | `REG_CTRL` | `CTRL` |

STATUS bits (одинаковые номера бит): RX_READY(0), TX_IDLE(1), TX_FULL(2), RX_FULL(3).  
FIFO depth: **8**. Запись в TX при полном FIFO: Python игнорирует; RTL держит `pready=0`.

## Timer (согласовано)

32-битный счётчик + 32-битный `period` (LO @+8, HI16 @+0xC), CTRL @+0x10.  
Дубликаты period @+0x18/+0x1C поддерживаются в Python; RTL `timer.sv` использует те же word-индексы для compare.

## SD (согласовано)

- **Block** (симулятор по умолчанию): LBA/DATA/CTRL/STATUS — см. `SdBlockRegs`.
- **SPI** (`--sd-spi`, TN9K FPGA profile): CMD/ARG/STATUS/… — см. `SdSpiRegs`.

Переключение в Python: `SystemBus(sd_spi=True)` или `use_sd_spi()`.

## Профили (YAML `profiles`)

| Профиль | SD режим | Назначение |
| ------- | -------- | ---------- |
| `sim_default` | block | CLI/GUI симулятор |
| `tn9k_fpga` | spi + Gowin backend | FPGA bring-up |

## Верификация согласованности

- `tests/peripherals/test_mmio_map_codegen.py` — offsets vs YAML
- `tests/peripherals/test_mmio.py`, `test_uart_fifo.py` — поведение Python
- `test/src/tb_uart_*.sv`, `tb_timer_gpio.sv` — RTL
- `test/compare_rtl_python.py`, `test/equiv/` — кросс-проверки (где применимо)

## Что менять при добавлении периферии

1. Добавить устройство в `docs/isa/mmio_map.yaml`.
2. Запустить `python scripts/gen_mmio.py`.
3. Подключить регион в `SystemBus` и RTL APB decoder.
4. Обновить [mmio.md](mmio.md) и при необходимости этот файл.
