# GDB remote debugging (E32C)

Отладка **функционального симулятора** через [GDB Remote Serial Protocol](https://sourceware.org/gdb/current/onlinedocs/gdb/Remote-Protocol.html) (TCP). Нативной архитектуры `e32c` в upstream GDB нет — работа по **адресам** (ELF/символы — [BACKLOG](../BACKLOG.md)).

Обзор проекта: [../../README.md](../../README.md).

---

## Запуск stub

```bash
pip install -e ".[dev]"
python -m cli.gdb_server --hex examples/smoke.hex --port 3333
```

Или после установки: `e32c-gdb-server --hex examples/smoke.hex`.

### Флаги сессии

Те же, что у `cli.debug` / GUI (`[cli.debug_common](../../src/cli/debug_common.py)`):


| Флаг                  | Описание                          |
| --------------------- | --------------------------------- |
| `--hex` / `--bin`     | Образ программы                   |
| `--load-addr`         | База загрузки (default 0)         |
| `--mmio`              | GPIO, UART, Timer, SD             |
| `--mmio-base`         | База MMIO (default `0xFFFF_0000`) |
| `--sd-image`          | Файл SD-образа                    |
| `--sd-create-sectors` | Создать образ N×512 B             |
| `--sd-spi`            | SD в режиме SPI-регистров         |
| `--host` / `--port`   | TCP (default `127.0.0.1:3333`)    |


---

## Подключение GDB

```bash
gdb -batch \
  -ex "target remote 127.0.0.1:3333" \
  -ex "info registers" \
  -ex "x/4wx 0" \
  -ex "stepi" \
  -ex "info registers pc"
```

Автотест (если `gdb` в PATH):

```bash
python examples/launch_gdb_smoke.py
```

---

## Регистры (RSP `g` / `p`)


| Индекс | Содержимое                            |
| ------ | ------------------------------------- |
| 0–31   | `r0`–`r31` (`r0` всегда 0 при чтении) |
| 32     | PC (дубликат `r31`)                   |
| 33     | flags (Intenable, Z, C, V, S)         |
| 34     | SPR: SAVED_IRQ_PC                     |
| 35     | SPR: IRQ_VECTOR                       |
| 36     | SPR: IRQ_MASK                         |


Кодировка в пакете: 8 hex-символов на регистр, little-endian.

Target XML: [e32c.xml](e32c.xml) (отдаётся через `qXfer:features:read`).

---

## Поддерживаемые пакеты (MVP)


| Пакет                 | Действие                                    |
| --------------------- | ------------------------------------------- |
| `?`                   | Причина остановки (`S05` trap, `S06` error) |
| `g` / `G`             | Читать / писать все регистры                |
| `p` / `P`             | Один регистр                                |
| `m` / `M`             | Память (hex bytes)                          |
| `c`                   | Continue до halt / breakpoint               |
| `s`                   | Один шаг                                    |
| `Z1` / `z1`           | Software breakpoint по адресу PC            |
| `k`                   | Завершить сессию                            |
| `qSupported`          | Возможности stub                            |
| `qXfer:features:read` | `e32c.xml`                                  |


Реализация: `[src/cli/gdb/](../../src/cli/gdb/)`.

---

## Ограничения

- Нет загрузки `.elf` и символов (только hex/bin).
- Нет OpenOCD / JTAG к RTL или плате.
- MMIO читается как обычная память (если включён `--mmio`).

Тесты: `[tests/cli/test_gdb_stub.py](../../tests/cli/test_gdb_stub.py)`.