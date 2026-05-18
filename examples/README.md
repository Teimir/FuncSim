# Examples (E32C)

Запуск из **корня репозитория** после `pip install -e ".[dev]"`.

Туториалы: [docs/tutorial/README.md](../docs/tutorial/README.md).

| Файл | Тип | Назначение | Команда | Туториал |
|------|-----|------------|---------|----------|
| `smoke.hex` | hex | ADDI/ADD/SUB/HALT | `python examples/launch_smoke.py` | [00](../docs/tutorial/00-setup-and-repo.md), [11](../docs/tutorial/11-cli-simulator.md) |
| `launch_smoke_gui.py` | py | GUI smoke | `python examples/launch_smoke_gui.py` [`--core tn9k`] | [13](../docs/tutorial/13-cli-debug-gui.md) |
| `launch_gdb_smoke.py` | py | GDB batch (нужен `gdb`) | `python examples/launch_gdb_smoke.py` | [14](../docs/tutorial/14-gdb-remote.md) |
| `device_demo.py` | py | MMIO GPIO/UART/Timer | `python examples/device_demo.py` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `device_demo_gui.py` | py | То же в GUI | `python examples/device_demo_gui.py` | [13](../docs/tutorial/13-cli-debug-gui.md) |
| `uart_calculator.py` | py | UART REPL в терминале | `python examples/uart_calculator.py` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `uart_calculator_gui.py` | py | UART в GUI | `python examples/uart_calculator_gui.py` | [13](../docs/tutorial/13-cli-debug-gui.md) |
| `sd_probe.py` | py | SD block read/write | `python examples/sd_probe.py` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `launch_sd_gui_demo.py` | py | SD + GUI | `python examples/launch_sd_gui_demo.py` | [13](../docs/tutorial/13-cli-debug-gui.md) |
| `sd_spi_probe.py` | py | SD SPI CMD sequence | `python examples/sd_spi_probe.py` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `launch_tn9k_demo.py` | py | UART + Timer + SD SPI (sim) | `python examples/launch_tn9k_demo.py` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `tn9k_demo_uart_timer_sd_*.asm` | asm | TN9K demo (handler @ 0x200) | `build_tn9k_firmware.py --profile demo` | [16](../docs/tutorial/16-rtl-cosim-fpga.md) |
| `sd_gui_demo.asm` | asm | Демо для SD GUI | через GUI + asm | [13](../docs/tutorial/13-cli-debug-gui.md) |
| `boot_smoke.asm` | asm | Минимальный boot test | `cli.sim --asm … --mmio` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `blink_uart.asm` | asm | UART blink (FPGA) | `gen_firmware_hex.py` | [16](../docs/tutorial/16-rtl-cosim-fpga.md) |
| `blink_uart_irq_main.asm` | asm | Main + timer IRQ | см. tutorial 15 | [15](../docs/tutorial/15-irq-timer-lab.md) |
| `blink_uart_irq_handler.asm` | asm | IRQ handler @ 0x100 | с main | [15](../docs/tutorial/15-irq-timer-lab.md) |
| `blink_uart_spam.asm` | asm | UART spam | FPGA / sim | [16](../docs/tutorial/16-rtl-cosim-fpga.md) |
| `demo_irq_timer.asm` | asm | Tutorial IRQ (lib) | `cli.sim --mmio --asm …` | [15](../docs/tutorial/15-irq-timer-lab.md) |
| `demo_sd_block.asm` | asm | SD block sector 0 | `--mmio --sd-image` | [10](../docs/tutorial/10-peripherals-mmio.md) |
| `launch_gdb_elf.py` | py | GDB + ELF | после сборки `link_e32c` | [14](../docs/tutorial/14-gdb-remote.md) |

### Общие флаги CLI

| Флаг | Описание |
|------|----------|
| `--hex` / `--bin` / `--elf` / `--asm` | Источник программы |
| `--load-addr` | База загрузки (hex/bin/asm) |
| `--mmio` | GPIO, UART, Timer, SD |
| `--sd-image` | Файл-образ SD |
| `--sd-spi` | Режим SPI @ +0x3000 |
| `--mmio-base` | Default `0xFFFF0000` |

См. [README.md](../README.md), [docs/mmio.md](../docs/mmio.md), [docs/tutorial/17-examples-walkthrough.md](../docs/tutorial/17-examples-walkthrough.md).
