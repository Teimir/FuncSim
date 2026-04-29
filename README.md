# E32C functional core (Python)

ISA spec: [docs/isa/spec.md](docs/isa/spec.md). Opcodes: [docs/isa/opcodes.yaml](docs/isa/opcodes.yaml).

## Dev

```bash
pip install -e ".[dev]"
pytest -q
```

## CLI

```bash
python -m cli.sim --help
python -m cli.debug --help
```

## Debugger GUI (tkinter)

```bash
python -m cli.debug_gui --help
# or, after install:
e32c-debug-gui --hex path/to/prog.hex --mmio
```

Load a `--bin` or `--hex` image, optional `--mmio` / `--mmio-base` (same as `cli.debug`). Use **File → Open** in the GUI to load without restarting.

