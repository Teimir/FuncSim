# 18 тАФ Troubleshooting / FAQ

## `ModuleNotFoundError: yaml` / `hypothesis`

```bash
pip install -e ".[dev]"
```

## `pytest` ╤Б╨╗╨╕╤И╨║╨╛╨╝ ╨┤╨╛╨╗╨│╨╕╨╣

```bash
pytest -q -m "not slow"
```

## `assemble error` / `unknown mnemonic`

- ╨Ю╨┤╨╜╨░ ╨╕╨╜╤Б╤В╤А╤Г╨║╤Ж╨╕╤П ╨╜╨░ ╤Б╤В╤А╨╛╨║╤Г.
- ╨Ш╨╝╨╡╨╜╨░ ╨╝╨╜╨╡╨╝╨╛╨╜╨╕╨║ ╨║╨░╨║ ╨▓ [opcodes.yaml](../isa/opcodes.yaml).
- ╨Т╨╡╤В╨║╨╕: `BEQ label` ╨╕╨╗╨╕ `BEQ 31 imm` ╨▓ ╨┐╤А╨╡╨┤╨╡╨╗╨░╤Е ┬▒1023 **╤Б╨╗╨╛╨▓**.

## `MisalignedAccess`

`LDR`/`STR` ╤В╨╛╨╗╤М╨║╨╛ ╨┐╤А╨╕ `addr % 4 == 0`.

## MMIO ╨╜╨╡ ╤А╨░╨▒╨╛╤В╨░╨╡╤В

╨Э╤Г╨╢╨╡╨╜ `--mmio` ╨╕╨╗╨╕ `--sd-image`. ╨Р╨┤╤А╨╡╤Б╨░ ╨╛╤В `0xFFFF0000` (default).

## UART ┬л╨╝╨╛╨╗╤З╨╕╤В┬╗ ╨▓ GUI

- ╨Т╨║╨╗╤О╤З╨╕╤В╨╡ `--mmio`.
- ╨Ф╨╗╤П ╨║╨░╨╗╤М╨║╤Г╨╗╤П╤В╨╛╤А╨░: ╤Б╤В╤А╨╛╨║╨░ ╤Б `\n`, ╨║╨╛╨╝╨░╨╜╨┤╨░ `HALT\n`.
- **Ctrl+U** тАФ ╨╛╤В╨┤╨╡╨╗╤М╨╜╨╛╨╡ ╨╛╨║╨╜╨╛ terminal.

## Timer IRQ ╨╜╨╡ ╤Б╤А╨░╨▒╨░╤В╤Л╨▓╨░╨╡╤В

1. `EI` ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜?
2. `WRITESPR` vector = ╨░╨┤╤А╨╡╤Б handler?
3. `PERIOD` ╨╕ `IRQ_EN` ╨▓ CTRL?
4. `IRQ_MASK` ╨╜╨╡ ╨▒╨╗╨╛╨║╨╕╤А╤Г╨╡╤В ╨╗╨╕╨╜╨╕╤О 0?

╨б╨╝. [15-irq-timer-lab.md](15-irq-timer-lab.md).

## GDB `Connection refused`

1. Stub ╨╖╨░╨┐╤Г╤Й╨╡╨╜: `python -m cli.gdb_server --hex тАж`
2. ╨Я╨╛╤А╤В 3333 ╤Б╨▓╨╛╨▒╨╛╨┤╨╡╨╜.
3. `target remote 127.0.0.1:3333`

## SD `NO_MEDIUM` / mount

GUI **Storage** тЖТ Browse тЖТ Mount, ╨╕╨╗╨╕ `--sd-image` ╨┐╤А╨╕ ╤Б╤В╨░╤А╤В╨╡.

## README timer vs mmio.md

╨Р╨║╤В╤Г╨░╨╗╤М╨╜╨░╤П ╨╝╨╛╨┤╨╡╨╗╤М: **32-bit COUNTER + PERIOD**, ╨╜╨╡ 64-bit LO/HI. ╨Ъ╨░╨╜╨╛╨╜: [mmio.md](../mmio.md).

## RTL / iverilog ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜

╨Ю╨┐╤Ж╨╕╨╛╨╜╨░╨╗╤М╨╜╨╛ ╨┤╨╗╤П [16-rtl-cosim-fpga.md](16-rtl-cosim-fpga.md). Python-╤В╤Г╤В╨╛╤А╨╕╨░╨╗╤Л ╤А╨░╨▒╨╛╤В╨░╤О╤В ╨▒╨╡╨╖ Verilog.

## ╨У╨┤╨╡ ╤Б╨┐╤А╨╛╤Б╨╕╤В╤М ╨┤╨░╨╗╤М╤И╨╡

- [BACKLOG.md](../BACKLOG.md) тАФ ╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╡ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П
- Issues ╤А╨╡╨┐╨╛╨╖╨╕╤В╨╛╤А╨╕╤П

