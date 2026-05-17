// GENERATED FILE — do not edit by hand.
// Source: docs/isa/mmio_map.yaml  |  Regenerate: python scripts/gen_mmio.py
// Included from RTL as: `include "mmio_generated.svh" (add -Itest/src to iverilog)

`ifndef E32C_MMIO_SD_REGS_SVH
`define E32C_MMIO_SD_REGS_SVH

// SD block mode @ +0x3000
`define E32C_SD_BLOCK_REG_CTRL 5'h0
`define E32C_SD_BLOCK_REG_STATUS 5'h1
`define E32C_SD_BLOCK_REG_LBA 5'h2
`define E32C_SD_BLOCK_REG_DATA 5'h4
`define E32C_SD_BLOCK_DATA_BYTES 512

// SD spi mode @ +0x3000
`define E32C_SD_SPI_REG_CTRL 5'h0
`define E32C_SD_SPI_REG_DIV 5'h1
`define E32C_SD_SPI_REG_CMD 5'h2
`define E32C_SD_SPI_REG_ARG 5'h3
`define E32C_SD_SPI_REG_RESP0 5'h4
`define E32C_SD_SPI_REG_STATUS 5'h5
`define E32C_SD_SPI_REG_BLKIDX 5'h6
`define E32C_SD_SPI_REG_DATAIX 5'h7
`define E32C_SD_SPI_REG_DATARD 5'h8
`define E32C_SD_SPI_REG_DATAWR 5'h9

`endif // E32C_MMIO_SD_REGS_SVH
