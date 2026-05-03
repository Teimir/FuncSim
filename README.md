# E32C functional core (Python)

ISA spec: [docs/isa/spec.md](docs/isa/spec.md). Opcodes: [docs/isa/opcodes.yaml](docs/isa/opcodes.yaml). Архитектура симулятора: [docs/architecture.md](docs/architecture.md).

## Dev

```bash
pip install -e ".[dev]"
pytest -q
python examples/launch_smoke.py
```

## CLI

```bash
python -m cli.sim --help
python -m cli.debug --help
```

## Debugger GUI (tkinter)

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

