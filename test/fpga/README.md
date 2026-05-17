# Tang Nano 9K — сборка FPGA (E32C SoC)

Плата: **Sipeed Tang Nano 9K**, FPGA **GW1NR-LV9QN88PC6/I5** (8640 LUT, 26 BSRAM).

---

## Память (только BSRAM, без внешней PSRAM)

| Регион | Адрес | Размер |
|--------|-------|--------|
| **Код + данные** | `0x0000_0000` | 8192 слов (32 KiB) |
| **Стек / heap** | `0x0000_8000` | 2048 слов (8 KiB) |
| **MMIO** | `0xFFFF_0000` | APB |

- **Инструкции:** `icache` читает из той же RAM, что и LDR/STR.
- **Boot:** образ из `firmware_b*.hex` → bank0 (`BOOT_INIT_MEMH=1` для Gowin).
- **Flash на плате** — только для битстрима (как всегда), не для программы.

Внешняя HyperRAM **не используется** (нет конфликта с MSPI/SSPI).

---

## Прошивка

Перед синтезом (обязательно после смены `.asm`):

```bash
python scripts/build_tn9k_firmware.py
# или полный демо UART+Timer+SD:
python scripts/build_tn9k_firmware.py --profile demo
```

Профили: `--profile blink` (по умолчанию, `BL` ~1 Hz), `hello` (сразу `Hi!`), `irq`, `smoke`, `sd_spi` (CMD0 + `OK`), `demo` (UART+Timer+SD → `USGR` + `T`…).

**Важно:** для сборки подойдут **`test/test.gprj`** или **`test/fpga/tn9k_soc.gprj`**. Перед синтезом: `python scripts/build_tn9k_firmware.py`. Без свежих `src/firmware_b*.hex` RAM пустая → UART молчит.

Терминал: **115200 8N1**, **8-bit** (не UTF-16), TX пин **17** (см. `tang_nano_9k.cst`).

**UART молчит:** `soc_top_tn9k` грузит прошивку из **`firmware_rom.svh`** (`BOOT_INIT_MEMH=0`). После `build_tn9k_firmware.py` обязательно **пересинтезируйте** bitstream — иначе в RAM старый/пустой образ. Для проверки линии UART: в `fpga_top_tn9k` временно `USE_HW_UART_STREAM=1` → на терминале поток `0x55`.

Если видите только `B` или `<0>L<0>` вместо `BL`: пересоберите прошивку (`build_tn9k_firmware.py`), в Gowin **Clean → Synthesize**. При мусоре в UART попробуйте в `soc_top_tn9k` параметр `UART_CLK_MHZ = 28` или `29`.

---

## Gowin

1. **`test/fpga/tn9k_soc.gprj`**
2. **Clean → Synthesize → Place & Route**
3. Top: `fpga_top_tn9k`

Цель: LUT &lt; 8640, BSRAM ≤ 26 блоков @ 27 MHz.

### microSD на TN9K (по умолчанию — MMIO shim)

**RP0006 / LUT overflow:** полный SoC + Gowin `SDIO_SPI_Top` не помещается в **8640 LUT** (~10k требуется). В `fpga_top_tn9k` по умолчанию **`SD_BACKEND=0`**: прошивка работает с **MMIO shim** (`apb_sd_spi`), пины TF — от shim.

| Режим | `SD_BACKEND` | Синтез TN9K | Карта |
|--------|----------------|-------------|--------|
| **Shim (рекомендуется)** | `0` | помещается | CMD/init по MMIO; SPI-пины 36–39 |
| Gowin IP | `1` | не помещается | включить `sdio_spi/*.v` в `tn9k_soc.gprj` |

- TF SPI в `tang_nano_9k.cst`: SCK=36, MOSI=37, CS_N=38, MISO=39.
- Прошивка demo: `build_tn9k_firmware.py --profile demo` → UART `USGRT…`, SD init + timer.
- Gowin IP (отдельный эксперимент): `test/src/sdio_spi/` — SDIO inouts не выводятся на top TN9K (слот только SPI 36–39).
