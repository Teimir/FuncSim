# Examples (E32C)

Запуск из **корня репозитория** после `pip install -e ".[dev]"`.

| Файл | Тип | Назначение | Команда |
|------|-----|------------|---------|
| `smoke.hex` | hex | ADDI/ADD/SUB/HALT | `python examples/launch_smoke.py` |
| `launch_smoke_gui.py` | py | GUI smoke | `python examples/launch_smoke_gui.py` |
| `launch_gdb_smoke.py` | py | GDB batch (нужен `gdb`) | `python examples/launch_gdb_smoke.py` |
| `device_demo.py` | py | MMIO GPIO/UART/Timer | `python examples/device_demo.py` |
| `device_demo_gui.py` | py | То же в GUI | `python examples/device_demo_gui.py` |
| `uart_calculator.py` | py | UART REPL в терминале | `python examples/uart_calculator.py` |
| `uart_calculator_gui.py` | py | UART в GUI | `python examples/uart_calculator_gui.py` |
| `sd_probe.py` | py | SD block read/write | `python examples/sd_probe.py` |
| `launch_sd_gui_demo.py` | py | SD + GUI | `python examples/launch_sd_gui_demo.py` |
| `sd_spi_probe.py` | py | SD SPI CMD sequence | `python examples/sd_spi_probe.py` |
| `launch_tn9k_demo.py` | py | UART + Timer + SD SPI (sim) | `python examples/launch_tn9k_demo.py` |
| `tn9k_demo_uart_timer_sd_*.asm` | asm | TN9K demo (handler @ 0x200) | `build_tn9k_firmware.py --profile demo` |
| `sd_gui_demo.asm` | asm | Демо для SD GUI | через GUI + asm |
| `boot_smoke.asm` | asm | Минимальный boot test | `cli.sim --asm …` |
| `blink_uart.asm` | asm | UART blink (FPGA) | `gen_firmware_hex.py` |
| `blink_uart_irq_main.asm` | asm | Main + timer IRQ | см. [tutorial_irq_timer.md](../docs/tutorial_irq_timer.md) |
| `blink_uart_irq_handler.asm` | asm | IRQ handler @ 0x100 | с main |
| `blink_uart_spam.asm` | asm | UART spam | FPGA / sim |
| `demo_irq_timer.asm` | asm | Tutorial IRQ (lib) | `cli.sim --mmio --asm …` |
| `demo_sd_block.asm` | asm | SD block sector 0 | `--mmio --sd-image` |
| `launch_gdb_elf.py` | py | GDB + ELF | после сборки `link_e32c` |

### Общие флаги CLI

| Флаг | Описание |
|------|----------|
| `--hex` / `--bin` / `--elf` / `--asm` | Источник программы |
| `--load-addr` | База загрузки (hex/bin/asm) |
| `--mmio` | GPIO, UART, Timer, SD |
| `--sd-image` | Файл-образ SD |
| `--sd-spi` | Режим SPI @ +0x3000 |
| `--mmio-base` | Default `0xFFFF0000` |

См. [README.md](../README.md), [docs/mmio.md](../docs/mmio.md).
