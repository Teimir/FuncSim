# RTL Memory Map (AXI4-Lite + APB)

APB base addresses and the AXI high-half route constant are generated from [`docs/isa/mmio_map.yaml`](../../docs/isa/mmio_map.yaml) into `mmio_generated.svh` (`python scripts/gen_mmio.py` from repo root). The register-detail tables below are descriptive; numeric bases must match the YAML.

- AXI RAM / boot RAM window: `0x0000_0000` .. `0x0000_0000 + RAM_WORDS*4 - 1` (TN9K: 256 words = 1 KiB, image from `firmware_rom.svh` on reset when `ENABLE_FW_BOOTLOAD=1`)
- APB window (through AXI-to-APB bridge): `0xFFFF_0000` .. `0xFFFF_FFFF`
- UART APB base: `0xFFFF_1000`
  - `+0x0`: `TXDATA` (W)
  - `+0x4`: `RXDATA` (R)
  - `+0x8`: `STATUS` (R) bit0=`RX_READY`, bit1=`TX_IDLE`
  - `+0xC`: `CTRL` (R/W) bit0=`IRQ_EN_RX`, bit1=`IRQ_EN_TX`, bit8=`RX_CLEAR`
- Timer APB base: `0xFFFF_2000`
  - `+0x0/+0x4`: `COUNTER_LO/HI` (R)
  - `+0x8/+0xC`: `COMPARE_LO/HI` (R/W)
  - `+0x10`: `CTRL` (R/W) bit0=`IRQ_EN`, bit1=`IRQ_PENDING`, bit2=`ACK(W1C)`
- SPI SD APB base: `0xFFFF_3000`
  - `+0x0`: `CTRL` (EN/CS_N/IRQ_EN/IRQ_CLR)
  - `+0x4`: `DIV`
  - `+0x8`: `TXDATA`
  - `+0xC`: `RXDATA`
  - `+0x10`: `STATUS` (BUSY/RX_VALID/TX_EMPTY/IRQ_PENDING)
- GPIO APB base: `0xFFFF_0000`
  - `+0x0`: `GPIO_OUT` (R/W)

Notes:
- `soc_top` uses one AXI master arbiter between external AXI host and core-side instruction/data access.
- APB decoder routes UART/Timer/GPIO/SPI-SD; IRQ lines from timer/uart/spi-sd are wired into the core IRQ input bus.
