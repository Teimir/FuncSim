# 17 — Каталог examples

Полная таблица: [examples/README.md](../../examples/README.md).


| Пример                   | Команда                                        | Что увидите                     |
| ------------------------ | ---------------------------------------------- | ------------------------------- |
| `launch_smoke.py`        | `python examples/launch_smoke.py`              | ADDI/ADD/SUB, halt, regs        |
| `launch_smoke_gui.py`    | `python examples/launch_smoke_gui.py`          | То же в GUI                     |
| `launch_gdb_smoke.py`    | `python examples/launch_gdb_smoke.py`          | GDB batch step                  |
| `device_demo.py`         | `python examples/device_demo.py`               | GPIO/UART/Timer MMIO            |
| `device_demo_gui.py`     | `python examples/device_demo_gui.py`           | MMIO вкладка                    |
| `uart_calculator.py`     | `python examples/uart_calculator.py`           | REPL: `8*8`, `HALT\n`           |
| `uart_calculator_gui.py` | `python examples/uart_calculator_gui.py`       | UART terminal                   |
| `sd_probe.py`            | `python examples/sd_probe.py`                  | SD block read/write             |
| `launch_sd_gui_demo.py`  | `python examples/launch_sd_gui_demo.py`        | SD + GUI Storage                |
| `sd_spi_probe.py`        | `python examples/sd_spi_probe.py`              | SPI CMD sequence                |
| `launch_tn9k_demo.py`    | `python examples/launch_tn9k_demo.py`          | UART+Timer+SD SPI               |
| `boot_smoke.asm`         | `cli.sim --mmio --asm …`                       | GPIO + UART 'K'                 |
| `blink_uart_irq_*.asm`   | см. [15-irq-timer-lab.md](15-irq-timer-lab.md) | Timer IRQ                       |
| `demo_sd_block.asm`      | `--mmio --sd-image`                            | Сектор 0                        |
| `launch_gdb_elf.py`      | после link ELF                                 | GDB + ELF (если есть toolchain) |


## Общие флаги


| Флаг                        | Назначение          |
| --------------------------- | ------------------- |
| `--hex` / `--bin` / `--asm` | Программа           |
| `--load-addr`               | База                |
| `--mmio`                    | Периферия           |
| `--sd-image`                | Образ SD            |
| `--sd-spi`                  | SPI (debug/GDB/GUI) |
| `--mmio-base`               | Default 0xFFFF0000  |


## Связь с туториалами


| Тема     | Глава                                            |
| -------- | ------------------------------------------------ |
| ISA labs | [asm/](asm/)                                     |
| MMIO     | [10-peripherals-mmio.md](10-peripherals-mmio.md) |
| GUI      | [13-cli-debug-gui.md](13-cli-debug-gui.md)       |
| GDB      | [14-gdb-remote.md](14-gdb-remote.md)             |
