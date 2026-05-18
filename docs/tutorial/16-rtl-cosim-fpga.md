# 16 — RTL, cosim и FPGA

Этот туториал — **маршрутизатор**. Детали в [test/README.md](../../test/README.md) и [test/fpga/README.md](../../test/fpga/README.md).

## Когда нужен RTL

- Проверка SoC на Verilog (UART, timer, SD SPI).
- Сравнение с Python: `test/compare_rtl_python.py`.
- Прошивка **Tang Nano 9K**.

## Быстрый smoke (Icarus)

Из корня (нужен `iverilog`):

```bash
python scripts/verify_all.py
```

Полный tier:

```bash
python scripts/verify_all.py --full
```

## MMIO в RTL

После правок YAML:

```bash
python scripts/gen_mmio.py
```

Генерирует `test/src/mmio_generated.svh`, `uart_regs.svh`, …

## Профили ядра


| Ядро | Файл           | Отличия       |
| ---- | -------------- | ------------- |
| full | `core.sv`      | MUL, LDREX    |
| TN9K | `core_tn9k.sv` | Без mul/LDREX |
| lite | `core_lite.sv` | Заглушка      |


См. [profiles.md](../profiles.md).

## FPGA

1. Собрать hex: `scripts/gen_firmware_hex.py`
2. Открыть `test/fpga/tn9k_soc.gprj` в Gowin IDE
3. Прошить плату — [test/fpga/README.md](../../test/fpga/README.md)

## Python ↔ RTL parity

- [core-full/06-parity-matrix.md](../core-full/06-parity-matrix.md)
- `test/equiv/` — YAML-программы для equiv-тестов

## Вернуться к симулятору

[00-setup-and-repo.md](00-setup-and-repo.md) · [11-cli-simulator.md](11-cli-simulator.md)