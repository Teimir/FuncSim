# Gowin SDIO_SPI IP (TN9K microSD)

Generated in Gowin Designer for **GW1NR-LV9QN88PC6/I5** (Tang Nano 9K).

| Setting | Value |
|---------|--------|
| Top module | `SDIO_SPI_Top` |
| Channel | **SPI1** (`O_spi1_cs_n`, not `O_spi_cs_n`) |
| I/O | **Disable I/O Insertion** (pads on `fpga_top_tn9k`) |
| Doc | **IPUG947** |

## Files

- `sdio_spi.v` — encrypted netlist (commit for reproducible builds)
- `sdio_spi.ipc` — generator settings
- `sdio_spi_tmp.v` — instantiation template

## SoC wiring

- Clocks: [`../sdio_spi_clocks.sv`](../sdio_spi_clocks.sv) from 27 MHz
- Wrapper: [`../sdio_spi_soc_wrapper.sv`](../sdio_spi_soc_wrapper.sv)
- MMIO: [`../apb_sdio_spi_bridge.sv`](../apb_sdio_spi_bridge.sv) → Python-aligned `apb_sd_spi` map
- Slot mux: [`../e32c_apb_sd_slot.sv`](../e32c_apb_sd_slot.sv) (`SD_BACKEND=0` shim / `1` Gowin pins)

The IP top does **not** export the internal `user_cpu_slave_reg_if` host port. Firmware uses the E32C MMIO shim; Gowin IP drives the TF SPI pins in parallel on FPGA.
