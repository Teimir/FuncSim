# RTL Memory Map (AXI4-Lite + APB)

## TN9K (FPGA)

| Region | Address | Backend |
|--------|---------|---------|
| RAM bank 0 | `0x0000_0000` .. +32 KiB | BSRAM — code + data after boot |
| RAM bank 1 | `0x0000_8000` .. +8 KiB | BSRAM |
| MMIO | `0xFFFF_0000` .. | APB |

Boot: `BOOT_INIT_MEMH` loads `firmware_b*.hex` into bank0 (Gowin). Fetch via `icache` from RAM.

## Simulation (`USE_FPGA_RAM=0`)

Unified `axi4lite_psram` model @ `0x0` — see `tb_psram_boot.sv`, `tb_boot_smoke.sv`.

MMIO: [../../docs/mmio.md](../../docs/mmio.md)

### APB peripherals (generated bases in `mmio_generated.svh`)

| Device | Base | Notes |
|--------|------|-------|
| GPIO | `0xFFFF_0000` | |
| UART | `0xFFFF_1000` | STATUS: bit0 RX ready, bit1 TX idle, bit2 TX full, bit3 RX full; FIFO depth 8 |
| Timer | `0xFFFF_2000` | |
| SD | `0xFFFF_3000` | `e32c_apb_sd_slot`: `SD_MMIO_MODE` 0=block (`sd_block.sv`), 1=SPI (`sd_spi.sv`); `SD_BACKEND` 0=shim, 1=Gowin IP pins (FPGA) |

Register offsets: `mmio_sd_regs.svh` (`scripts/gen_mmio.py` from `docs/isa/mmio_map.yaml`).
