# TN9K hello baseline (зафиксировано)

Проверено на **Tang Nano 9K**, UART **115200 8N1**, TX pin **17**.

## Ожидаемый вывод

После reset (один раз), HEX:

```text
48 69 21 0D 0A
```

ASCII: `Hi!` + CRLF (5 байт).

## RTL / SoC

| Параметр | Значение |
|----------|----------|
| Top | `fpga_top_tn9k` |
| `TN9K_PROFILE_DEMO` | `0` |
| `ENABLE_SD_SPI` / `ENABLE_TIMER` | `0` (UART-only) |
| `SD_USE_CARD_MEM` | `0` |
| Прошивка | `examples/tn9k_uart_hello.asm` → `FW_WORDS=15` |

Критичные исправления RTL: `icache` + адрес выборки `core_dbg_pc`, FSM `if_req_valid` в `FETCH_WAIT`.

## Восстановить прошивку baseline в `test/src/`

```bash
python scripts/restore_tn9k_baseline.py
# или
python scripts/build_tn9k_firmware.py --profile hello --install-baseline
```

## Синтез (Gowin)

1. `python scripts/restore_tn9k_baseline.py`
2. Проект `test/test.gprj` или `test/fpga/tn9k_soc.gprj`
3. Top `fpga_top_tn9k`, параметр **`TN9K_PROFILE_DEMO = 0`**
4. Clean → Synthesize → Program

Цель LUT: **&lt; ~7200** (запас до 8640).

## Файлы в этой папке

Копия артефактов `hello` (`firmware_rom.svh`, `firmware_b0..b3.hex`) на момент фиксации baseline.
