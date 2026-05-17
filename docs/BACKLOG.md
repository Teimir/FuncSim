# Deferred epics (out of interpreter coverage MVP)

Track as GitHub issues when prioritised:

| Epic | Estimate | Start when |
|------|----------|------------|
| GDB remote stub for E32C | 2–3 weeks | External users need GDB without Tk GUI |
| ELF loader / linker integration | 2–4 weeks | GCC or LLVM target for E32C exists |
| Cycle-accurate timing vs `core.sv` | 3+ weeks | Microarch contract is frozen |
| `execute.py` dispatch table refactor | 3–5 days | ISA grows past ~55 opcodes |
| Python SD SPI protocol model (6b) | 2–4 weeks | Block MMIO insufficient for driver debug |
| Cython / Rust hot-path accelerator | 1–2 weeks | Profiling shows >1M steps/run in CI |
