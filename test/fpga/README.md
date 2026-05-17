# Tang Nano 9K FPGA Build

Target device: `GW1NR-LV9QN88PC6/I5` (8640 LUT limit).

## Which project to open

| Project | Use for board? |
|---------|----------------|
| **`test/fpga/tn9k_soc.gprj`** | **Yes** — fits in ~8k LUT |
| `test/test.gprj` | Simulation / full SoC (too large for TN9K) |

**Top module:** `fpga_top_tn9k`  
**SoC:** `soc_top_tn9k` — `fetch_rom_nop.svh` + **data BRAM** bank0 **8K words** @ `0x0`, bank1 **4K words** @ `0x8000` (~24/26 BSRAM). Optional `TN9K_IF_ROM_BRAM=1` needs byte-lane hex (see `instr_fetch_rom.sv`).

**Does not fit on TN9K:** `core.sv`, PSRAM boot copy (`firmware_rom.svh`), AXI instruction fetch (`icache`).

## Before synthesis (required)

```bash
python scripts/gen_firmware_hex.py --asm examples/blink_uart_irq_main.asm --handler examples/blink_uart_irq_handler.asm --handler-addr 0x100 --words 128 --if-rom-words 512
```

This updates **`fetch_rom_nop.svh`** (used by the CPU) and hex/rom files for sim.

Quick UART smoke (`K` only):

```bash
python scripts/gen_firmware_hex.py --asm examples/boot_smoke.asm --words 128
```

## Gowin GUI

1. Open `test/fpga/tn9k_soc.gprj`.
2. **Project → Clean** → Synthesize.
3. Place&Route → **Use DONE as regular IO**.
4. Top: `fpga_top_tn9k`, `USE_HW_UART_STREAM = 0`.

## UART

- 115200 8N1 (`tang_nano_9k.cst`: TX=17, RX=18).
- IRQ demo: periodic `BL\n` (~1 s timer).
- Handler @ **0x100** (must match `WRITESPR` in main.asm).

## Tcl

```tcl
cd <repo>/test/fpga
source build_tn9k.tcl
```
