# Deferred epics (out of interpreter coverage MVP)

Track as GitHub issues when prioritised.

**Scope note:** каталог `test/` (RTL, cosim, FPGA, `tb_*`) в текущем цикле **не меняем**. Работа ведётся в `src/`, `docs/`, `examples/`, опционально `tests/` (pytest). См. [profiles.md](profiles.md).

| Epic | Estimate | Start when | Status |
|------|----------|------------|--------|
| GDB remote stub for E32C | 2–3 weeks | External users need GDB without Tk GUI | **Done (MVP)** — `cli.gdb_server`, [gdb/README.md](gdb/README.md) |
| ELF loader / linker integration | 2–4 weeks | GCC or LLVM target for E32C exists | **In progress** — spec in roadmap; code pending agent mode |
| Cycle-accurate timing vs `core.sv` | 3+ weeks | Microarch contract is frozen | Open (`test/` only) |
| `execute.py` dispatch table refactor | 3–5 days | ISA grows past ~55 opcodes | Open |
| Python SD SPI protocol model | 2–4 weeks | Block MMIO insufficient for driver debug | **Done** — `SdSpiMmio`, `--sd-spi` |
| Cython / Rust hot-path accelerator | 1–2 weeks | Profiling shows >1M steps/run in CI | Open |

## Out of scope (documented gaps)

- Расширение `test/compare_rtl_python.py` и RTL cosim — пока `test/` заморожен.
- OpenOCD / JTAG к FPGA — отдельно от Python GDB stub.
- Коммит локального TN9K WIP в `test/` — вне текущего цикла.

**UARTexampleGOWIN/:** задокументирован как пример Gowin ([UARTexampleGOWIN/README.md](../UARTexampleGOWIN/README.md)); в репозитории оставлен, не удаляется.
