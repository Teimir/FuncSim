# 11 — Пакетный симулятор (`cli.sim`)

Исходник: `[src/cli/sim.py](../../src/cli/sim.py)`.

## Базовый запуск

```bash
python -m cli.sim --hex examples/smoke.hex --until-halt
python -m cli.sim --asm docs/tutorial/asm/lab_fundamentals.asm --until-halt --dump-regs
```

## Все флаги


| Флаг                    | Описание                                          |
| ----------------------- | ------------------------------------------------- |
| `--load-addr ADDR`      | База загрузки (default 0)                         |
| `--hex PATH`            | Образ: слово hex на строку                        |
| `--bin PATH`            | Raw LE                                            |
| `--asm PATH`            | Сборка asm на лету                                |
| `--max-steps N`         | Лимит шагов (default 100000)                      |
| `--until-halt`          | До HALT (в пределах max-steps)                    |
| `--cycles-report`       | *(нет отдельного вывода — cycles в строке итога)* |
| `--dump-regs`           | Печать r0…r31 и flags                             |
| `--dump-gpio`           | GPIO_OUT (включает MMIO bus)                      |
| `--mmio`                | SystemBus: GPIO/UART/Timer/SD                     |
| `--mmio-base ADDR`      | База MMIO (default 0xFFFF0000)                    |
| `--sd-image PATH`       | Файл-образ SD (подразумевает MMIO)                |
| `--sd-create-sectors N` | Создать/обрезать образ N×512 B                    |
| `--cycle-ns FLOAT`      | approx_ns = cycles × ns                           |
| `--uart-stdout`         | Зеркалировать UART TX в stdout                    |
| `--trace`               | Строка на каждую инструкцию                       |
| `--trace-file PATH`     | Тот же trace в файл                               |
| `--break ADDR`          | Breakpoint PC (повторяемый)                       |


**Примечание:** `--sd-spi` в `cli.sim` нет; режим SPI — в `cli.debug` / GUI / GDB через `debug_common`.

## Примеры

### Trace

```bash
python -m cli.sim --hex examples/smoke.hex --trace --max-steps 5
```

### Breakpoint

```bash
python -m cli.sim --hex examples/smoke.hex --break 0x8 --max-steps 20
```

### MMIO + UART

```bash
python -m cli.sim --mmio --asm examples/boot_smoke.asm --uart-stdout --max-steps 50000
```

### SD образ

```bash
python -m cli.sim --mmio --sd-image /tmp/disk.img --sd-create-sectors 64 --asm examples/demo_sd_block.asm --max-steps 200000
```

## Вывод

```
steps=N halted=True cycles=C
```

При `--dump-regs` — таблица регистров. При `--cycle-ns 10` — `approx_ns=…`.

## Дальше

[12-cli-debug-repl.md](12-cli-debug-repl.md) · [13-cli-debug-gui.md](13-cli-debug-gui.md)