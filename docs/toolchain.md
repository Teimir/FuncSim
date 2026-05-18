# E32C toolchain (Python)

Полный цикл **ассемблирование → линковка → ELF/bin/hex → симулятор / GDB** без внешнего GCC/LLVM.

## Установка

```bash
pip install -e ".[dev]"
```

Команды в `PATH`: `e32c-asm`, `e32c-ld`, `e32c-objcopy`, `e32c-cc`, `e32c-gdb-server`.

## Быстрый пример

```bash
# Один файл → hex на stdout
e32c-asm examples/smoke.asm -o examples/smoke.hex

# Main + IRQ handler → ELF
e32c-ld -o build/blink.elf \
  examples/blink_uart_irq_main.asm@0 \
  examples/blink_uart_irq_handler.asm@0x100

# Драйвер: asm + link → ELF или bin
e32c-cc -o build/smoke.elf examples/smoke.asm
e32c-cc -O binary -o build/smoke.bin examples/smoke.asm

# ELF → hex для симулятора
e32c-objcopy build/smoke.elf build/smoke.hex -O ihex

# Симулятор / GDB
python -m cli.sim --elf build/smoke.elf --until-halt --dump-regs
e32c-gdb-server --elf build/smoke.elf --port 3333
```

## Формат ELF

| Поле | Значение |
|------|----------|
| Class | ELF32 |
| Endian | little |
| `e_machine` | `0xE32C` (EM_E32C) |
| `e_type` | ET_EXEC |
| Сегменты | PT_LOAD, выровненные 32-битные слова |

Символы (`.symtab`) опциональны; `e32c-ld --symbol name=addr` добавляет глобальные метки.

## Прошивка FPGA

```bash
e32c-ld -o /tmp/fw.elf main.asm@0 handler.asm@0x100
python scripts/gen_firmware_hex.py --elf /tmp/fw.elf --words 256 --skip-fetch-rom
```

## Опциональный LLVM

Скрипт `scripts/build_llvm.sh` собирает **upstream LLVM 19** (target X86) в `toolchain/llvm-build/`. Это **не** бэкенд E32C; для ISA используйте Python-инструменты выше. LLVM-бэкенд `e32c` — отдельный эпик ([BACKLOG.md](BACKLOG.md)).
