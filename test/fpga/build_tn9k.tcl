# Tang Nano 9K: fetch_rom_nop + core_tn9k + BRAM (~8k LUT). Regenerate firmware before synth.
set_device GW1NR-LV9QN88PC6/I5
add_file ../src/fpga_top_tn9k.sv
add_file ../src/soc_top_tn9k.sv
add_file ../src/top.sv
add_file ../src/core_tn9k.sv
add_file ../src/csr_irq.sv
add_file ../src/ram.sv
add_file ../src/axi4lite_ram_dual.sv
# instr_fetch_rom optional (set TN9K_IF_ROM_BRAM=1 in soc_top_tn9k); needs firmware_b*.hex
# add_file ../src/instr_fetch_rom.sv
add_file ../src/firmware_b0.hex
add_file ../src/firmware_b1.hex
add_file ../src/firmware_b2.hex
add_file ../src/firmware_b3.hex
add_file ../src/axi4lite_xbar_1x2.sv
add_file ../src/axi_to_apb_bridge.sv
add_file ../src/apb_decoder.sv
add_file ../src/gpio.sv
add_file ../src/timer.sv
add_file ../src/uart.sv
add_file ../src/uart_tx.v
add_file ../src/uart_rx.v
add_file tang_nano_9k.cst
set_option -top_module fpga_top_tn9k
set_option -use_mspi_as_gpio 1
run all
