# MMIO map (E32C)

Источник истины: `[docs/isa/mmio_map.yaml](isa/mmio_map.yaml)`.

Регенерация:

```bash
python scripts/gen_mmio.py
```

→ `[src/core/mmio_constants.py](../src/core/mmio_constants.py)`, `[test/src/mmio_generated.svh](../test/src/mmio_generated.svh)`.

Обзор и сводная карта: [../README.md](../README.md#карта-адресов).

---

## Общие правила


| Параметр          | Значение                                                 |
| ----------------- | -------------------------------------------------------- |
| База по умолчанию | `0xFFFF_0000` (`MMIO_BASE_DEFAULT`)                      |
| Размер окна       | `0x4000` (16 KiB)                                        |
| Доступ            | Только **32-битные выровненные** слова (`addr % 4 == 0`) |
| Маршрутизация     | `SystemBus` (Python): RAM, затем MMIO                    |


---

## Расположение устройств


| Смещение  | Устройство | Размер (Python) | Абсолютный адрес |
| --------- | ---------- | --------------- | ---------------- |
| `+0x0000` | GPIO       | 4 B             | `0xFFFF_0000`    |
| `+0x1000` | UART       | 16 B            | `0xFFFF_1000`    |
| `+0x2000` | Timer      | 32 B            | `0xFFFF_2000`    |
| `+0x3000` | SD         | 528 B           | `0xFFFF_3000`    |


---

## GPIO (`+0x0000`)


| +offset | Доступ | Описание                   |
| ------- | ------ | -------------------------- |
| `0x00`  | R/W    | 32-битная выходная защёлка |


---

## UART (`+0x1000`)

Модель: `[src/core/peripherals/uart.py](../src/core/peripherals/uart.py)`. RTL: `[test/src/uart.sv](../test/src/uart.sv)`.


| +offset | Имя    | Доступ | Описание                      |
| ------- | ------ | ------ | ----------------------------- |
| `0x00`  | TX     | W      | Младший байт → TX-очередь     |
| `0x04`  | RX     | R      | Байт из RX (пусто → 0)        |
| `0x08`  | STATUS | R      | bit0 RX ready; bit1 TX idle; bit2 TX full; bit3 RX full |
| `0x0C`  | CTRL   | R/W    | bit0 IRQ RX; bit1 IRQ TX done |

TX/RX FIFO depth **8** (запись в TX при full — stall APB `pready=0` в RTL).


---

## Timer (`+0x2000`)

Модель: [`src/core/peripherals/timer.py`](../src/core/peripherals/timer.py).

### LO / HI = одно 64-битное значение

MMIO доступно только **32-битными словами**. Счётчик и compare внутри модели — **64-bit**; в карте регистров они разбиты на пару LO/HI (как в типичных APB-таймерах).

| +offset | Имя        | Доступ | Биты |
| ------- | ---------- | ------ | ---- |
| `0x00`  | COUNTER_LO | R      | [31:0] счётчика |
| `0x04`  | COUNTER_HI | R      | [63:32] счётчика |
| `0x08`  | COMPARE_LO | R/W    | [31:0] порога |
| `0x0C`  | COMPARE_HI | R/W    | [63:32] порога |
| `0x10`  | CTRL       | R/W    | IRQ_EN, PENDING, ACK (W1C) |

**Согласованное чтение счётчика:** сначала `COUNTER_HI`, затем `COUNTER_LO` — симулятор фиксирует снимок на чтении HI (см. код таймера).

**CTRL:** bit0 `IRQ_EN`; bit1 `PENDING` (read); bit2 `ACK` (W1C).

При `cycles >= compare` и включённых IRQ CPU — см. [peripherals.md](peripherals.md), [tutorial_irq_timer.md](tutorial_irq_timer.md).

---

## SD storage (`+0x3000`)

Два режима на одном смещении (флаг `**--sd-spi`** / `SystemBus(sd_spi=True)`).

### A. Block device (по умолчанию)

Модель: `[src/core/peripherals/sd_card.py](../src/core/peripherals/sd_card.py)`.


| +offset        | Имя    | Доступ                                                |
| -------------- | ------ | ----------------------------------------------------- |
| `0x00`         | CTRL   | W: `1`=read sector, `2`=write, `3`=flush              |
| `0x04`         | STATUS | R: READY(1), ERROR(4), NO_MEDIUM(8); err в bits 16–23 |
| `0x08`         | LBA    | R/W: индекс сектора                                   |
| `0x10`–`0x20C` | DATA   | 128 слов = 512 B буфер                                |


**Чтение:** LBA → CTRL=1 → ждать READY → читать DATA.  
**Запись:** LBA → заполнить DATA → CTRL=2.

Образ — файл на хосте (`--sd-image`), размер кратен 512.

### B. SPI command registers (`--sd-spi`)

Модель: `[src/core/peripherals/sd_spi.py](../src/core/peripherals/sd_spi.py)`. RTL: `[test/src/sd_spi.sv](../test/src/sd_spi.sv)`.


| +offset | Имя                               |
| ------- | --------------------------------- |
| `0x00`  | CTRL (EN, CS_N, IRQ_EN, IRQ_CLR)  |
| `0x04`  | DIV                               |
| `0x08`  | CMD (+ bit8 START)                |
| `0x0C`  | ARG                               |
| `0x10`  | RESP0                             |
| `0x14`  | STATUS (BUSY, READY, RX_VALID, …) |
| `0x18`  | BLKIDX                            |
| `0x1C`  | DATAIX                            |
| `0x20`  | DATARD                            |
| `0x24`  | DATAWR                            |


Типичная инициализация: CMD0 → CMD8 → CMD55 → CMD41 → CMD17/24. Пример: `[examples/sd_spi_probe.py](../examples/sd_spi_probe.py)`.

---

## CLI


| Флаг                  | Эффект                                  |
| --------------------- | --------------------------------------- |
| `--mmio`              | Включить `SystemBus`                    |
| `--mmio-base`         | База окна                               |
| `--sd-image`          | Смонтировать образ (подразумевает MMIO) |
| `--sd-create-sectors` | Создать образ N секторов                |
| `--sd-spi`            | Режим SPI вместо block                  |


Применяется в: `cli.sim`, `cli.debug`, `cli.debug_gui`, `cli.gdb_server`.