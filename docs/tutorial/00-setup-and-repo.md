# 00 — Установка и карта репозитория

## Требования

- Python **3.10+**
- Git
- (Опционально) **Icarus Verilog** — для RTL из [16-rtl-cosim-fpga.md](16-rtl-cosim-fpga.md)
- (Опционально) **GDB** — для [14-gdb-remote.md](14-gdb-remote.md)

## Установка Python-пакета

Из корня репозитория:

```bash
pip install -e ".[dev]"
```

Проверка:

```bash
python -m cli.sim --hex examples/smoke.hex --until-halt --dump-regs
python examples/launch_smoke.py
```

Ожидание: `halted=True`, `r2=0xa`, `r3=0xf`, `r4=0x19`, `r5=0x5`.

## Тесты

```bash
pytest -q -m "not slow"
```

Полный прогон (дольше):

```bash
pytest -q
python scripts/verify_all.py
python scripts/verify_all.py --full
```

## Карта каталогов


| Путь             | Назначение                                            |
| ---------------- | ----------------------------------------------------- |
| `src/core/`      | ISA: decode, execute, state, memory, bus, peripherals |
| `src/cli/`       | `sim`, `debug`, `debug_gui`, `gdb_server`, `asm`      |
| `docs/isa/`      | `spec.md`, `opcodes.yaml`, `mmio_map.yaml`            |
| `docs/tutorial/` | Эта серия туториалов                                  |
| `examples/`      | Готовые hex/asm и launch-скрипты                      |
| `tests/`         | pytest (ISA, MMIO, CLI, GDB)                          |
| `test/`          | RTL SystemVerilog, cosim, FPGA                        |
| `scripts/`       | `gen_mmio.py`, `verify_all.py`, `gen_firmware_hex.py` |


## Точки входа CLI


| Команда                                        | Модуль          |
| ---------------------------------------------- | --------------- |
| `python -m cli.sim`                            | Пакетный прогон |
| `python -m cli.debug`                          | REPL-отладчик   |
| `python -m cli.debug_gui` / `e32c-debug-gui`   | Tk GUI          |
| `python -m cli.gdb_server` / `e32c-gdb-server` | GDB stub        |
| `python -m cli.asm`                            | Ассемблер в hex |


## Следующий шаг

[01-isa-fundamentals.md](01-isa-fundamentals.md) или сразу [11-cli-simulator.md](11-cli-simulator.md), если ISA уже знакомы.