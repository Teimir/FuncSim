# Профили E32C: Python, RTL, FPGA

Краткая матрица «кто что реализует». Полная **карта возможностей** и **адресов** — в [главном README](../README.md).

---

## Сводная таблица

| Профиль | Где | ISA | Память / fetch | Отладка | CI |
|---------|-----|-----|----------------|---------|-----|
| **Python** | `src/core/` | Полная (51 mnem) | `Memory` / `SystemBus` | REPL, GUI, GDB | pytest, equiv |
| **RTL full** | `test/src/core.sv` | Полная + mul | AXI, icache, `soc_top` | TB / waves | verify_all; `tb_core_isa` в `--full` |
| **RTL TN9K** | `test/src/core_tn9k.sv` | Без mul/LDREX; subset ALU/mem | comb IF ROM 96w, dual RAM | TB smoke | локально |
| **FPGA TN9K** | `test/fpga/tn9k_soc.gprj` | Как TN9K | `fetch_rom_nop` @ 27 MHz | UART на плате | **manual** |
| **RTL sim top** | `test/test.gprj` | `core.sv` | Полный SoC | Icarus | не на 9K LUT |

---

## Python

- Семантика: [isa/spec.md](isa/spec.md)
- **Вариант ядра:** `--core full|tn9k|lite` в `cli.sim`, `cli.debug`, `cli.debug_gui`, `cli.gdb_server` (illegal opcodes как в RTL-профиле; SPR CORE_INFO/FEATURES согласованы)
- MMIO: block SD или `--sd-spi`
- Cosim: [test/compare_rtl_python.py](../test/compare_rtl_python.py) — 3–4 smoke-теста

## RTL

- Full core (arch/microarch): [core-full/README.md](core-full/README.md)
- Карта: [test/src/rtl_memory_map.md](../test/src/rtl_memory_map.md)
- Документация каталога: [test/README.md](../test/README.md)
- SD: `SD_MMIO_MODE` block или SPI; `SD_BACKEND=SHIM` (Icarus) / `GOWIN_IP` (TN9K + `SDIO_SPI_Top`)
- UART: TX/RX FIFO depth 8, STATUS TX_FULL/RX_FULL

## FPGA

- Только **`test/fpga/tn9k_soc.gprj`**
- [test/fpga/README.md](../test/fpga/README.md)

## Пример Gowin UART

- [UARTexampleGOWIN/README.md](../UARTexampleGOWIN/README.md) — не часть e32c-sim CI
