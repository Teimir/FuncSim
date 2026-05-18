# 14 — GDB Remote

Полная справка: [gdb/README.md](../gdb/README.md). Реализация: `src/cli/gdb/`.

## Запуск stub

Терминал 1:

```bash
python -m cli.gdb_server --hex examples/smoke.hex --port 3333
# e32c-gdb-server --hex examples/smoke.hex --mmio
```


| Флаг                                 | Описание                 |
| ------------------------------------ | ------------------------ |
| `--host`                             | Bind (default 127.0.0.1) |
| `--port`                             | TCP (default 3333)       |
| `--hex` / `--bin`                    | Программа                |
| `--load-addr`                        | База                     |
| `--mmio`                             | Периферия                |
| `--mmio-base`                        | MMIO base                |
| `--sd-image` / `--sd-create-sectors` | SD                       |
| `--sd-spi`                           | SPI SD                   |


## GDB (терминал 2)

```bash
gdb -batch \
  -ex "target remote 127.0.0.1:3333" \
  -ex "info registers" \
  -ex "x/4wx 0" \
  -ex "stepi" \
  -ex "info registers pc"
```

Интерактивно: `target remote :3333`, затем `stepi`, `continue`, `break *0x10`, `x/8wx 0xffff1000` (MMIO).

## Регистры GDB (индексы stub)


| Индекс | Содержимое                 |
| ------ | -------------------------- |
| 0–31   | r0–r31                     |
| 32     | PC                         |
| 33     | flags                      |
| 34–36  | SPR saved PC, vector, mask |


## Пакеты RSP (MVP)


| Пакет                 | Действие            |
| --------------------- | ------------------- |
| `?`                   | Stop reason         |
| `g` / `G`             | Все регистры        |
| `p` / `P`             | Один регистр        |
| `m` / `M`             | Память (hex bytes)  |
| `c`                   | Continue            |
| `s`                   | Step                |
| `Z1` / `z1`           | Software breakpoint |
| `k`                   | Kill                |
| `qSupported`          | Capabilities        |
| `qXfer:features:read` | Target XML          |


## Автотесты

```bash
python examples/launch_gdb_smoke.py
python examples/launch_gdb_elf.py   # после сборки ELF (если настроено)
```

## MMIO + GDB

```bash
python -m cli.gdb_server --mmio --hex examples/smoke.hex
```

Чтение UART: `x/4wx 0xffff1000` (при default base).

## Ограничения

- Нет native `e32c` target в upstream GDB без XML.
- Нет ELF-символов в stub (BACKLOG).
- Нет JTAG к RTL/плате.

## Дальше

[15-irq-timer-lab.md](15-irq-timer-lab.md) · [18-troubleshooting-faq.md](18-troubleshooting-faq.md)