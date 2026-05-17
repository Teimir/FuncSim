//Copyright (C)2014-2025 Gowin Semiconductor Corporation.
//All rights reserved.
//File Title: Template file for instantiation
//Tool Version: V1.9.12 (64-bit)
//Part Number: GW1NR-LV9QN88PC6/I5
//Device: GW1NR-9
//Device Version: C
//Created Time: Sun May 17 22:47:34 2026

//Change the instance name and port connections to the signal names
//--------Copy here to design--------

	SDIO_SPI_Top your_instance_name(
		.I_clk(I_clk), //input I_clk
		.I_rst_n(I_rst_n), //input I_rst_n
		.I_sdio_2M_clk(I_sdio_2M_clk), //input I_sdio_2M_clk
		.I_sdio_cpu_clk(I_sdio_cpu_clk), //input I_sdio_cpu_clk
		.I_sdio_clk(I_sdio_clk), //input I_sdio_clk
		.IO_sdio_cmd(IO_sdio_cmd), //inout IO_sdio_cmd
		.IO_sdio_dat0(IO_sdio_dat0), //inout IO_sdio_dat0
		.IO_sdio_dat1_irq(IO_sdio_dat1_irq), //inout IO_sdio_dat1_irq
		.IO_sdio_dat2_rw(IO_sdio_dat2_rw), //inout IO_sdio_dat2_rw
		.IO_sdio_dat3_cd(IO_sdio_dat3_cd), //inout IO_sdio_dat3_cd
		.O_spi1_cs_n(O_spi1_cs_n), //output O_spi1_cs_n
		.O_spi_sclk(O_spi_sclk), //output O_spi_sclk
		.O_spi_mosi(O_spi_mosi), //output O_spi_mosi
		.I_spi_miso(I_spi_miso) //input I_spi_miso
	);

//--------Copy end-------------------
