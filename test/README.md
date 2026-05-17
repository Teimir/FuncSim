# E32C — RTL, симуляция и cosim

Каталог **`test/`** — SystemVerilog-модели, testbench для **Icarus Verilog**, сопоставление с Python-симулятором и проекты **Gowin** для платы.

Главный обзор репозитория: [../README.md](../README.md).  
Карта адресов MMIO (YAML): [../docs/isa/mmio_map.yaml](../docs/isa/mmio_map.yaml).  
Прошивка Tang Nano 9K: [fpga/README.md](fpga/README.md).

---

## Что внутри

```
test/
├── src/                 # RTL-модули и testbench (*.sv)
├── fpga/                # tn9k_soc.gprj, Tcl, constraints
├── equiv/               # Python-only программы (yaml)
├── compare_rtl_python.py
├── iverilog_soc_psram.f # file list для SoC-bench
└── test.gprj            # TN9K SoC (как tn9k_soc.gprj; пути src/, fpga/tang_nano_9k.cst)
```

---

## Карта возможностей RTL

| Компонент | Файлы | Назначение |
|-----------|-------|------------|
| **Ядро full** | `core.sv`, `mul_dsp.sv` | Полная ISA, умножение, IRQ |
| **Ядро TN9K** | `core_tn9k.sv` | Урезание: без mul, без LDREX/STREX; extra decode stage |
| **Ядро lite** | `core_lite.sv` | Заглушка (без data AXI) |
| **CSR** | `csr_spr.sv` | IRQ, SPR 0–5 (identity RO) |
| **Память** | `ram.sv`, `axi4lite_ram*.sv`, `psram.sv` | AXI RAM, PSRAM-модель |
| **Кэш** | `icache.sv` | Instruction fetch (full SoC) |
| **Шина** | `axi_to_apb_bridge.sv`, `apb_decoder.sv`, `axi4lite_xbar_1x2.sv` | AXI → APB |
| **Периферия** | `gpio.sv`, `uart.sv`, `timer.sv`, `e32c_apb_sd_slot.sv` | APB slaves; SD: block (`sd_block.sv`) или SPI (`sd_spi.sv`) |
| **SD / microSD** | `apb_sdio_spi_bridge.sv`, `sdio_spi_soc_wrapper.sv`, `sdio_spi/` | MMIO shim + Gowin `SDIO_SPI_Top` на FPGA |
| **UART PHY** | `uart_tx.v`, `uart_rx.v` | Из референса Gowin |
| **Top sim** | `top.sv` | Параметризуемый SoC (USE_TN9K_CORE, …) |
| **Top FPGA** | `fpga_top_tn9k.sv`, `soc_top_tn9k.sv` | Плата TN9K |
| **Прошивка** | `firmware_b*.hex`, `fetch_rom_nop.svh` | IF ROM / boot |

---

## Карта адресов (RTL)

Сгенерированные константы: `src/mmio_generated.svh` (`python scripts/gen_mmio.py`).

Подробная таблица: [`src/rtl_memory_map.md`](src/rtl_memory_map.md).

| Регион | Адрес | Примечание |
|--------|-------|------------|
| AXI RAM | `0x0000_0000` + | Слова; размер зависит от top |
| TN9K bank0 | `0x0000_0000` | 8192 слов |
| TN9K bank1 | `0x0000_8000` | 2048 слов |
| MMIO (APB) | `0xFFFF_0000` … | Через AXI→APB |
| GPIO | `0xFFFF_0000` | `GPIO_OUT` |
| UART | `0xFFFF_1000` | TX/RX/STATUS (FIFO depth 8) / CTRL |
| Timer | `0xFFFF_2000` | Counter, compare, CTRL |
| SD | `0xFFFF_3000` | Block или SPI MMIO (`e32c_apb_sd_slot`, `SD_MMIO_MODE`) |

---

## Testbench (основные)

| Bench | Что проверяет |
|-------|----------------|
| `tb_ram.sv` | RAM |
| `tb_icache.sv` | I-cache |
| `tb_axi_apb_uart.sv` | AXI + APB + UART |
| `tb_uart_loopback.sv` | UART loopback |
| `tb_uart_fifo.sv` | UART TX burst + STATUS TX_IDLE |
| `tb_psram_boot.sv` | Boot из PSRAM |
| `tb_boot_smoke.sv` | Boot smoke |
| `tb_core_irq.sv` | IRQ в ядре |
| `tb_core_isa.sv` | ISA subset (nightly) |
| `tb_core_tn9k_smoke.sv` | TN9K + illegal mul |
| `tb_soc_longrun.sv` | Длинный прогон SoC |
| `tb_timer_gpio.sv` | Timer + GPIO |
| `tb_irq_flow.sv` | Цепочка IRQ |
| `tb_sd_spi.sv`, `tb_sd_spi_protocol.sv` | SD SPI shim |
| `tb_sd_block.sv` | SD block-mode MMIO |
| `tb_sd_backend_smoke.sv` | `SD_BACKEND=SHIM`, CMD0 + STATUS |
| `tb_equiv_basic.sv` | Cosim с Python |

Запуск в CI: [`scripts/verify_all.py`](../scripts/verify_all.py).

---

## Локальная симуляция

```bash
# RAM
iverilog -g2012 -o test/out_tb_ram.vvp test/src/tb_ram.sv test/src/ram.sv
vvp test/out_tb_ram.vvp

# I-cache
iverilog -g2012 -o test/out_tb_icache.vvp test/src/tb_icache.sv test/src/icache.sv
vvp test/out_tb_icache.vvp

# SoC + UART (из корня репо)
iverilog -g2012 -f test/iverilog_soc_psram.f -o test/out_tb_axi_apb_uart.vvp test/src/tb_axi_apb_uart.sv
cd test/src && vvp ../out_tb_axi_apb_uart.vvp
```

Ожидайте в stdout строку вида `tb_axi_apb_uart PASS`.

---

## Cosim Python ↔ RTL

```bash
python test/compare_rtl_python.py           # 3 проверки
python test/compare_rtl_python.py --full    # + tb_core_isa
```

Python-эквивалентность программ (без RTL): `python -m test.equiv --all`.

---

## Проекты Gowin

| Проект | Назначение |
|--------|------------|
| **`fpga/tn9k_soc.gprj`** | **Плата** Tang Nano 9K |
| `test.gprj` | Большой SoC + `core.sv` (симуляция / синтез не на 9K) |

См. [fpga/README.md](fpga/README.md): частота, пины UART, `gen_firmware_hex.py`.

---

## Связь с Python

| Аспект | Python | RTL |
|--------|--------|-----|
| ISA | [docs/isa/spec.md](../docs/isa/spec.md) | `core.sv` / `core_tn9k.sv` |
| MMIO layout | [mmio_map.yaml](../docs/isa/mmio_map.yaml) | `mmio_generated.svh` |
| SD | block default; `--sd-spi` | `sd_spi.sv` |
| Отладка | GDB, GUI, REPL | waves / $display в TB |

Полная автоматическая сверка всей ISA **не** выполняется — только smoke в `compare_rtl_python.py`.
