// GENERATED FILE — do not edit by hand.
// Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py
// Included from RTL as: `include "mmio_generated.svh" (add -Itest/src to iverilog)

`ifndef E32C_MMIO_GENERATED_SVH
`define E32C_MMIO_GENERATED_SVH

`define E32C_MMIO_BASE 32'hffff0000
`define E32C_MMIO_AXI_HIGH 16'hffff

// GPIO: full 32-bit base + 4 KiB decode page (paddr[31:12])
`define E32C_GPIO_BASE 32'hffff0000
`define E32C_GPIO_PAGE 20'hffff0

// UART: full 32-bit base + 4 KiB decode page (paddr[31:12])
`define E32C_UART_BASE 32'hffff1000
`define E32C_UART_PAGE 20'hffff1

// TIMER: full 32-bit base + 4 KiB decode page (paddr[31:12])
`define E32C_TIMER_BASE 32'hffff2000
`define E32C_TIMER_PAGE 20'hffff2

// SD_SPI: full 32-bit base + 4 KiB decode page (paddr[31:12])
`define E32C_SD_SPI_BASE 32'hffff3000
`define E32C_SD_SPI_PAGE 20'hffff3

`endif // E32C_MMIO_GENERATED_SVH
