# E32C functional core (Python)

ISA spec: [docs/isa/spec.md](docs/isa/spec.md). Opcodes: [docs/isa/opcodes.yaml](docs/isa/opcodes.yaml). MMIO bases (Python + RTL): [docs/isa/mmio_map.yaml](docs/isa/mmio_map.yaml). Архитектура симулятора: [docs/architecture.md](docs/architecture.md). Соглашение ABI: **R30 = SP**, **R31 = PC** (в ассемблере доступны псевдо **CMP**, **CMN**, **MOV**, **TST** — см. spec).

After changing MMIO layout, edit `docs/isa/mmio_map.yaml` and run `python scripts/gen_mmio.py` to refresh `src/core/mmio_constants.py` and `test/src/mmio_generated.svh`. CI verifies they match the YAML.

## Dev

```bash
pip install -e ".[dev]"
pytest -q -m "not slow"
python examples/launch_smoke.py
```

### Full verification

```bash
python scripts/verify_all.py          # quick: unit tests + RTL smoke
python scripts/verify_all.py --full   # + slow Hypothesis, long RTL, co-sim
```

| Tier | Python | RTL | FPGA |
|------|--------|-----|------|
| PR / `verify_all --quick` | pytest (excl. `slow`), ruff, MMIO codegen, `test.equiv` | ram, icache, UART, loopback, IRQ, SD, `compare_rtl_python` | manual |
| Nightly / `--full` | all pytest incl. `slow` | + `tb_core_isa`, longrun, timer_gpio, irq_flow, `compare_rtl_python --full` | manual ([test/fpga/README.md](test/fpga/README.md)) |

Optional: `python scripts/verify_all.py --quick --coverage` (requires `pytest-cov`, target 85% on `core`).

## CLI

```bash
python -m cli.sim --help
python -m cli.debug --help
```

## Debugger GUI (tkinter)

Implementation lives under `src/cli/debug_gui/`; session flags (`--hex`, `--bin`, `--mmio`, `--sd-image`, …) are shared with the text debugger via `cli.debug_common`.

```bash
python -m cli.debug_gui --help
python examples/launch_smoke_gui.py
python examples/launch_sd_gui_demo.py
python examples/uart_calculator.py
python examples/uart_calculator_gui.py
# or, after install:
e32c-debug-gui --hex path/to/prog.hex --mmio
```

Load a `--bin` or `--hex` image, optional `--mmio` / `--mmio-base` (same as `cli.debug`). Optional **`--sd-image`** / **`--sd-create-sectors`** attach a 512-byte-sector file (see [docs/mmio.md](docs/mmio.md)). Use **File → Open** in the GUI to load without restarting; **Storage** tab mounts SD images when MMIO is on.

## RTL (AXI4-Lite/APB) smoke flow

SystemVerilog SoC prototypes live in `test/src/` and include:
- `e32c_core` with IRQ/CSR baseline and ISA subset execution
- AXI4-Lite RAM + AXI-to-APB bridge + APB UART/Timer/GPIO
- I-cache frontend and integration top (`soc_top`)

Local RTL checks:

```bash
iverilog -g2012 -o test/out_tb_ram.vvp test/src/tb_ram.sv test/src/ram.sv
vvp test/out_tb_ram.vvp

iverilog -g2012 -o test/out_tb_icache.vvp test/src/tb_icache.sv test/src/icache.sv
vvp test/out_tb_icache.vvp

iverilog -g2012 -f test/iverilog_soc_psram.f -o test/out_tb_axi_apb_uart.vvp test/src/tb_axi_apb_uart.sv
(cd test/src && vvp ../out_tb_axi_apb_uart.vvp)
```

Basic RTL/Python equivalence smoke:

```bash
python test/compare_rtl_python.py
```