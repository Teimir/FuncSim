set_device GW1NR-LV9QN88PC6/I5
add_file ../src/fpga_bringup_tn9k.sv
add_file ../src/uart_stream_test.sv
add_file tang_nano_9k_bringup.cst
set_option -top_module fpga_bringup_tn9k
set_option -use_mspi_as_gpio 1
run all
