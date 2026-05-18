# 12 — REPL-отладчик (`cli.debug`)

```bash
python -m cli.debug --hex examples/smoke.hex
```

Флаги сессии (общие с GUI/GDB): `[debug_common.py](../../src/cli/debug_common.py)`


| Флаг                    | Описание                |
| ----------------------- | ----------------------- |
| `--load-addr`           | База загрузки           |
| `--hex` / `--bin`       | Образ (один обязателен) |
| `--mmio`                | Периферия               |
| `--mmio-base`           | База MMIO               |
| `--sd-image`            | SD файл                 |
| `--sd-create-sectors N` | Создать образ           |
| `--sd-spi`              | SD в режиме SPI         |


## Команды REPL


| Команда              | Действие                                  |
| -------------------- | ----------------------------------------- |
| `s`                  | Один шаг                                  |
| `c [N]`              | До N шагов (default 10000) или halt/break |
| `r`                  | GPR + flags + cycles                      |
| `x ADDR [COUNT]`     | Hex dump COUNT слов                       |
| `dis [ADDR] [COUNT]` | Дизассемблер (default PC, 8)              |
| `b ADDR`             | Breakpoint                                |
| `bl`                 | Список breakpoints                        |
| `bc`                 | Сброс всех breakpoints                    |
| `q` / Ctrl+D         | Выход                                     |
| `help`               | Справка                                   |


## Сценарий

```
e32c> s
e32c> r
e32c> dis 0 4
e32c> b 0x10
e32c> c
```

## MMIO

```bash
python -m cli.debug --hex examples/smoke.hex --mmio
```

Для SD:

```bash
python -m cli.debug --mmio --sd-image /tmp/sd.img --sd-create-sectors 32
```

## Дальше

[13-cli-debug-gui.md](13-cli-debug-gui.md) — графический интерфейс.