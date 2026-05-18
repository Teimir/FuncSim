# TN9K demo: UART + Timer + SD (MMIO shim)

Полный демо-профиль для TF-карты и периодического таймера.

## Сборка

```bash
python scripts/build_tn9k_firmware.py --profile demo
```

Прошивка: `examples/tn9k_demo_uart_timer_sd_main.asm` + handler `@0x200`.  
В FPGA main патчится таймер (~1 Hz @ 27 MHz): `640` / `410` вместо `2000` / `0`.

## Синтез (Gowin)

1. Прошивка **demo** (см. выше).
2. Top `fpga_top_tn9k`, параметр **`TN9K_PROFILE_DEMO = 1`**  
   (включает `ENABLE_SD_SPI` и `ENABLE_TIMER`).
3. `SD_USE_CARD_MEM = 0`, `SD_BACKEND = 0` (только MMIO shim).
4. Clean → Synthesize → Place & Route → Program.

Ориентир LUT: **~8000–8500** (должно быть **&lt; 8640**). При **RP0006** — убедиться, что `TN9K_PROFILE_DEMO=1` только для demo, не смешивать с hello-прошивкой при `DEMO=0`.

## Пины microSD (SPI)

| Сигнал | Pin (CST) |
|--------|-----------|
| SCK | 36 |
| MOSI | 37 |
| CS_N | 38 |
| MISO | 39 |

## UART

**115200 8N1**, 8-bit. После reset (подождать ~1–3 с на SD init):

| Этап | Байты (пример) |
|------|----------------|
| Баннер | `US` … |
| SD OK | `G` |
| Timer armed | `R` |
| IRQ ticks | `T` `T` … |

Без карты: возможен `E` (`sd_fail`) вместо `G`, таймер всё равно может дать `R` и `T`.

## Симуляция (Python)

```bash
pytest tests/integration/test_asm_programs.py::test_tn9k_demo_uart_timer_sd -q
```

## Переключение hello ↔ demo

| Профиль | Firmware build | `TN9K_PROFILE_DEMO` |
|---------|----------------|---------------------|
| hello | `--profile hello` | `0` |
| demo | `--profile demo` | `1` |

Всегда пересобирайте прошивку и bitstream парой (не hello-ROM + demo-SoC).
