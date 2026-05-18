# TN9K verification suite

Isolated tests for Tang Nano 9K SoC under Icarus Verilog and Python.

## Layout

- `links/` — mirror of DUT, firmware, examples, docs (symlink or copy via `materialize.py`)
- `rtl/` — testbenches only
- `python/` — pytest
- `cosim/` — Python ↔ RTL lockstep
- `hw/` — board serial checks (manual / self-hosted CI)

## Hello baseline (board-verified)

UART `Hi!\r\n` @ 115200 — см. [baseline/README.md](baseline/README.md). Восстановить прошивку: `python scripts/restore_tn9k_baseline.py`.

## Demo (UART + Timer + SD)

Сборка и Gowin `TN9K_PROFILE_DEMO=1`: [DEMO.md](DEMO.md).

## Quick start

From repository root:

```bash
python test/tn9k/scripts/materialize.py --mode auto
python scripts/build_tn9k_firmware.py --profile hello
python test/tn9k/scripts/materialize.py --force
python test/tn9k/run_all.py --quick
```

## Tiers

| Command | Contents |
|---------|----------|
| `--quick` | pytest (not slow), 5 RTL smoke benches, cosim subset |
| `--full` | all pytest, all RTL benches, full cosim (50+ programs) |
| `--exhaustive` | slow tests, longrun, optional `--hw --port COMx` |

## HW

Program the board (`test/fpga/tn9k_soc.gprj`), then:

```bash
python test/tn9k/hw/run_matrix.py --port COM3 --profile hello
```

See [hw/README.md](hw/README.md) and [links/fpga/README.md](links/fpga/README.md) after materialize.
