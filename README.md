# E32C — функциональный симулятор и RTL-прототип SoC

Репозиторий **e32c-sim**: учебно-инженерная платформа вокруг 32-битной ISA **E32C** — функциональный интерпретатор на Python, SystemVerilog-модели ядра и периферии, сборка под **Tang Nano 9K** (Gowin GW1NR-9).


| Документ                                                 | Содержание                         |
| -------------------------------------------------------- | ---------------------------------- |
| [docs/isa/spec.md](docs/isa/spec.md)                     | Семантика ISA (канон для Python)   |
| [docs/isa/opcodes.yaml](docs/isa/opcodes.yaml)           | Кодировки мнемоник (51 инструкция) |
| [docs/architecture.md](docs/architecture.md)             | Архитектура симулятора             |
| [docs/mmio.md](docs/mmio.md)                             | MMIO, регистры устройств           |
| [docs/profiles.md](docs/profiles.md)                     | Python vs RTL vs FPGA              |
| [docs/BACKLOG.md](docs/BACKLOG.md)                       | Отложенные эпики                   |
| [docs/toolchain.md](docs/toolchain.md)                   | Тулчейн: asm, ld, ELF, objcopy     |
| [test/README.md](test/README.md)                         | RTL, testbench, cosim              |
| [test/fpga/README.md](test/fpga/README.md)               | Прошивка платы                     |
| [docs/gdb/README.md](docs/gdb/README.md)                 | GDB Remote stub                    |
| [docs/tutorial/README.md](docs/tutorial/README.md) | **Туториалы** (ISA, ядро, MMIO, GUI, GDB) |
| [examples/README.md](examples/README.md)               | Каталог примеров и команд          |
| [UARTexampleGOWIN/README.md](UARTexampleGOWIN/README.md) | Референс UART Gowin                |


**ABI:** **R30 = SP**, **R31 = PC (IP)**. Псевдоинструкции ассемблера: **CMP**, **CMN**, **MOV**, **TST** — см. [spec](docs/isa/spec.md).

---

## Структура репозитория

```
E32C/
├── src/                    # Python: ядро, CLI, GUI, GDB stub
│   ├── core/               # ISA, память, MMIO, runner
│   └── cli/                # sim, debug, debug_gui, gdb_server
├── tests/                  # pytest (ISA, периферия, CLI)
├── test/                   # RTL (Icarus), cosim, FPGA-проекты
│   ├── src/                # core.sv, soc_top, UART, SD SPI, …
│   └── fpga/               # tn9k_soc.gprj
├── docs/                   # Спеки, MMIO, GDB, профили
├── examples/               # .hex, .asm, launch-скрипты
├── scripts/                # verify_all, gen_mmio, gen_firmware_hex
└── UARTexampleGOWIN/       # Отдельный пример Gowin UART (не CI)
```

---

## Карта возможностей

### ISA и ядро


| Возможность                        | Python (`src/core`) | RTL `core.sv` | RTL `core_tn9k` | FPGA TN9K   |
| ---------------------------------- | ------------------- | ------------- | --------------- | ----------- |
| 51 мнемоника E32C                  | да                  | да            | да (кроме mul)  | как TN9K    |
| MUL / SMUL / UMULL / SMULL / MLA   | да                  | да            | **illegal**     | **illegal** |
| LDREX / STREX                      | да                  | да            | **illegal**     | **illegal** |
| Флаги Z/C/V/S, ADDS/SUBS           | да                  | да            | да              | да          |
| IRQ + SPR (vector, mask, saved PC) | да                  | да            | да              | да          |
| Точки останова / watchpoints       | да                  | —             | —               | —           |
| GDB Remote (TCP RSP)               | да                  | —             | —               | —           |
| ELF / символы                      | нет (BACKLOG)       | —             | —               | —           |


### Память и шина


| Возможность                      | Python                    | RTL SoC             | FPGA TN9K    |
| -------------------------------- | ------------------------- | ------------------- | ------------ |
| Линейная RAM (слова)             | `Memory`, размер задаётся | AXI RAM / dual bank | 8K + 2K слов |
| MMIO окно 16 KiB @ `0xFFFF_0000` | `SystemBus`               | APB decode          | APB          |
| GPIO                             | да                        | да                  | да           |
| UART 8N1                         | очереди TX/RX             | APB + `uart_*.v`    | HW UART      |
| Timer → IRQ                      | cycle counter             | `timer.sv`          | да           |
| SD block (LBA + 512 B buffer)    | по умолчанию              | —                   | —            |
| SD SPI (CMD 0/8/55/41/17/24)     | `--sd-spi`                | `sd_spi.sv`         | —            |
| I-cache                          | —                         | `icache.sv`         | нет (IF ROM) |


### Инструменты


| Инструмент                         | Назначение                         |
| ---------------------------------- | ---------------------------------- |
| `python -m cli.sim`                | Пакетный прогон, лимит шагов       |
| `python -m cli.debug`              | REPL: step, regs, mem, breakpoints |
| `e32c-debug-gui` / `cli.debug_gui` | Tk: память, дизасм, MMIO, SD       |
| `python -m cli.gdb_server`         | GDB `target remote :3333`          |
| `python -m cli.asm`                | Минимальный ассемблер              |
| `scripts/verify_all.py`            | pytest + RTL smoke (+ `--full`)    |


---

## Карта адресов

### Программная RAM (линейная)

В **симуляторе** базовый адрес загрузки задаётся `--load-addr` (по умолчанию `0`). Размер RAM — при создании `Memory()` (типично весь адресуемый диапазон теста).


| Регион          | Адреса (типично) | Python                            | RTL / FPGA                                   |
| --------------- | ---------------- | --------------------------------- | -------------------------------------------- |
| Основная RAM    | `0x0000_0000` …  | `Memory.read_word` / `write_word` | AXI slave, TN9K: bank0 @ 0, bank1 @ `0x8000` |
| Загрузка образа | с `load_addr`    | `--hex`, `--bin`                  | `firmware_*.hex`, boot copy                  |


Доступ только **выровненными 32-битными словами** (`addr % 4 == 0`), little-endian.

### MMIO (источник: [docs/isa/mmio_map.yaml](docs/isa/mmio_map.yaml))

База по умолчанию: `**0xFFFF_0000`**, размер окна: `**0x4000`**. После правок YAML: `python scripts/gen_mmio.py` → `src/core/mmio_constants.py`, `test/src/mmio_generated.svh`.

```
0xFFFF_0000  +------------------+  GPIO_OUT (4 B)
             | (reserved)       |
0xFFFF_1000  +------------------+  UART
0xFFFF_2000  +------------------+  Timer
0xFFFF_3000  +------------------+  SD (block или SPI)
0xFFFF_4000  (конец окна MMIO)
```


| Смещение от `mmio_base` | Устройство | Размер (Python) | Абсолютный адрес (default) |
| ----------------------- | ---------- | --------------- | -------------------------- |
| `+0x0000`               | GPIO       | 4 B             | `0xFFFF_0000`              |
| `+0x1000`               | UART       | 16 B            | `0xFFFF_1000`              |
| `+0x2000`               | Timer      | 32 B            | `0xFFFF_2000`              |
| `+0x3000`               | SD storage | 528 B           | `0xFFFF_3000`              |


#### UART (`+0x1000`)


| +offset | Имя    | Доступ | Описание                    |
| ------- | ------ | ------ | --------------------------- |
| `0x00`  | TX     | W      | байт в TX-очередь           |
| `0x04`  | RX     | R      | байт из RX                  |
| `0x08`  | STATUS | R      | bit0 RX ready, bit1 TX idle |


#### Timer (`+0x2000`)


| +offset | Имя | Доступ |
| ------- | --- | ------ |
| `0x00` | COUNTER | R — 32-bit счётчик |
| `0x04` | COUNTER_HI_PAD | R — 0 |
| `0x08` / `0x0C` | PERIOD_LO / PERIOD_HI | R/W — порог |
| `0x10` | CTRL | R/W — IRQ_EN, PENDING, ACK (W1C) |


#### SD @ `+0x3000` — режим **block** (по умолчанию)


| +offset        | Имя    | Описание                                 |
| -------------- | ------ | ---------------------------------------- |
| `0x00`         | CTRL   | W: `1` read sector, `2` write, `3` flush |
| `0x04`         | STATUS | READY, ERROR, NO_MEDIUM                  |
| `0x08`         | LBA    | индекс сектора                           |
| `0x10`–`0x20C` | DATA   | буфер 512 B (128 слов)                   |


#### SD @ `+0x3000` — режим **SPI** (`--sd-spi`)

Регистры как RTL `apb_sd_spi`: CTRL, DIV, CMD, ARG, RESP0, STATUS, BLKIDX, DATAIX, DATARD, DATAWR — см. [docs/mmio.md](docs/mmio.md), [test/src/sd_spi.sv](test/src/sd_spi.sv).

### SPR (специальные регистры)


| Индекс | Имя                               | Python            |
| ------ | --------------------------------- | ----------------- |
| 0      | SAVED_IRQ_PC                      | R/W               |
| 1      | IRQ_VECTOR                        | R/W               |
| 2      | IRQ_MASK                          | R/W               |
| 3–5    | CORE_INFO, ISA_REVISION, FEATURES | RO (вариант ядра) |


---

## Быстрый старт (Python)

```bash
pip install -e ".[dev]"
pytest -q -m "not slow"
python examples/launch_smoke.py
python -m cli.debug_gui --hex examples/smoke.hex
```

Полная проверка:

```bash
python scripts/verify_all.py          # quick: pytest + RTL smoke
python scripts/verify_all.py --full   # + slow Hypothesis, tb_core_isa, …
```


| Tier               | Python              | RTL                                     | FPGA                                       |
| ------------------ | ------------------- | --------------------------------------- | ------------------------------------------ |
| PR / `--quick`     | pytest −slow, equiv | ram, icache, UART, IRQ, SD, cosim smoke | вручную                                    |
| Nightly / `--full` | + Hypothesis slow   | + longrun, timer_gpio, irq_flow         | [test/fpga/README.md](test/fpga/README.md) |


---

## Python-симулятор (`src/`)

Цикл **fetch → decode → execute** (`[core/runner.py](src/core/runner.py)`), декод из `[docs/isa/opcodes.yaml](docs/isa/opcodes.yaml)`.


| Модуль                                                     | Роль                               |
| ---------------------------------------------------------- | ---------------------------------- |
| `[core/state.py](src/core/state.py)`                       | 32 GPR, flags, SPR, halt           |
| `[core/execute.py](src/core/execute.py)`                   | Семантика инструкций               |
| `[core/memory.py](src/core/memory.py)`                     | Линейная RAM                       |
| `[core/bus.py](src/core/bus.py)`                           | RAM + MMIO (GPIO, UART, Timer, SD) |
| `[core/debug_controller.py](src/core/debug_controller.py)` | Шаг, run, снимки для GUI/GDB       |
| `[core/peripherals/](src/core/peripherals/)`               | Модели устройств                   |


**CLI:** `--hex` / `--bin`, `--mmio`, `--mmio-base`, `--sd-image`, `--sd-create-sectors`, `--sd-spi`.

**Примеры:** `examples/launch_smoke.py`, `launch_smoke_gui.py`, `device_demo.py`, `sd_spi_probe.py`, `uart_calculator.py`, `launch_gdb_smoke.py`.

Подробнее: [docs/architecture.md](docs/architecture.md).

---

## RTL и FPGA (`test/`)

SystemVerilog: ядро, AXI4-Lite RAM, APB GPIO/UART/Timer/SD-SPI, tops для симуляции и платы.


| Артефакт        | Файл / каталог                                             |
| --------------- | ---------------------------------------------------------- |
| Полное ядро     | `[test/src/core.sv](test/src/core.sv)`                     |
| Ядро под TN9K   | `[test/src/core_tn9k.sv](test/src/core_tn9k.sv)`           |
| SoC (симуляция) | `[test/src/top.sv](test/src/top.sv)`, `soc_top`            |
| SoC (плата)     | `[test/src/soc_top_tn9k.sv](test/src/soc_top_tn9k.sv)`     |
| Карта RTL       | `[test/src/rtl_memory_map.md](test/src/rtl_memory_map.md)` |


**Симуляция (Icarus):** см. [test/README.md](test/README.md).

**Плата:** открыть `[test/fpga/tn9k_soc.gprj](test/fpga/tn9k_soc.gprj)` — не `test/test.gprj` (не влезает в LUT).

**Cosim:** `[test/compare_rtl_python.py](test/compare_rtl_python.py)` — узкий smoke Python↔RTL (3–4 проверки).

---

## Отладка


| Способ | Команда / ссылка                                                                     |
| ------ | ------------------------------------------------------------------------------------ |
| Tk GUI | `e32c-debug-gui --hex prog.hex --mmio`                                               |
| REPL   | `python -m cli.debug --hex prog.hex`                                                 |
| GDB    | `python -m cli.gdb_server --hex prog.hex` → [docs/gdb/README.md](docs/gdb/README.md) |


---

## См. также

- **Профили и расхождения Python/RTL:** [docs/profiles.md](docs/profiles.md)
- **Референс Gowin UART (не E32C CI):** [UARTexampleGOWIN/README.md](UARTexampleGOWIN/README.md)
- **Roadmap:** [docs/BACKLOG.md](docs/BACKLOG.md)

