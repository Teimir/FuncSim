# UARTexampleGOWIN — референс Gowin (UART)

Отдельный **учебный проект Gowin IDE** для UART на **Tang Nano 9K**. Не входит в Python-симулятор E32C и не запускается через `verify_all` / `pytest`.

| | |
|--|--|
| Обзор E32C | [../README.md](../README.md) |
| RTL UART в SoC | [../test/src/uart_tx.v](../test/src/uart_tx.v), [uart_rx.v](../test/src/uart_rx.v), [uart.sv](../test/src/uart.sv) |
| FPGA SoC E32C | [../test/fpga/README.md](../test/fpga/README.md) |

---

## Назначение

- Показать минимальный **UART TX/RX 8N1** на GW1NR-9.
- Исходники `uart_tx.v` / `uart_rx.v` — эталон для копий в `test/src/` (см. заголовки файлов).

---

## Содержимое

| Путь | Описание |
|------|----------|
| [uart/uart.gprj](uart/uart.gprj) | Проект Gowin (device GW1NR-LV9QN88PC6/I5) |
| [uart/src/uart_top.v](uart/src/uart_top.v) | Top: тактирование, UART |
| [uart/src/uart_tx.v](uart/src/uart_tx.v) | Передатель |
| [uart/src/uart_rx.v](uart/src/uart_rx.v) | Приёмник |
| [uart/src/top.cst](uart/src/top.cst) | Pin constraints |
| uart/impl/ | Отчёты synthesis/P&R (опционально в git) |
| uart/example_*.fs | Готовые bitstream (опционально) |

---

## Сборка

1. [Gowin EDA](https://www.gowinsemi.com/en/support/download_eda/)
2. Открыть **`uart/uart.gprj`**
3. Synthesize → Place & Route → Program Device
4. Скорость и пины — в `uart_top.v` и `top.cst`

---

## Сравнение с E32C

| Компонент | UARTexampleGOWIN | E32C |
|-----------|------------------|------|
| CPU E32C | нет | Python / `core_tn9k` |
| UART | standalone | MMIO @ `0xFFFF_1000` + APB в RTL |
| CI | нет | `verify_all`, pytest |

При архивировании вне репозитория сохраните `uart/src/*.v`, `uart.gprj` и этот README.
