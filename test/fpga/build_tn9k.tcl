# Tang Nano 9K SoC (matches tn9k_soc.gprj). Before: python scripts/build_tn9k_firmware.py
set_device -name GW1NR-9C GW1NR-LV9QN88PC6/I5
add_file ../src/fpga_top_tn9k.sv
add_file ../src/soc_top_tn9k.sv
add_file ../src/top.sv
add_file ../src/core_tn9k.sv
add_file ../src/icache.sv
add_file ../src/csr_spr.sv
add_file ../src/ram.sv
add_file ../src/axi4lite_ram_dual.sv
add_file ../src/firmware_b0.hex
add_file ../src/firmware_b1.hex
add_file ../src/firmware_b2.hex
add_file ../src/firmware_b3.hex
add_file ../src/axi4lite_xbar_1x2.sv
add_file ../src/axi_to_apb_bridge.sv
add_file ../src/apb_decoder.sv
add_file ../src/sd_spi.sv
add_file ../src/sd_spi_card_mem.sv
add_file ../src/apb_sdio_spi_bridge.sv
add_file ../src/e32c_apb_sd_slot.sv
add_file ../src/gpio.sv
add_file ../src/timer.sv
add_file ../src/uart.sv
add_file ../src/uart_tx.v
add_file ../src/uart_rx.v
add_file tang_nano_9k.cst
set_option -top_module fpga_top_tn9k
set_option -verilog_std sysv2017
set_option -use_mspi_as_gpio 1
run all
exit
