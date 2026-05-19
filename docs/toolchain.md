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

## LLVM (experimental backend)

Экспериментальный таргет **E32C** в LLVM 19 (форк в дереве + патчи Triple/ELF):

```bash
# Клонирует llvm-project при первом запуске, ставит lib/Target/E32C, собирает llvm-mc
bash scripts/build_llvm.sh

# Только установить/обновить таргет в уже клонированном llvm-project:
bash scripts/install_e32c_llvm_target.sh
```

Бинарники: `toolchain/llvm-build-e32c/bin/llvm-mc`, `llc`, …

Синтаксис asm для `llvm-mc`: регистры с префиксом `r` (`ADD r1 r2 r3`, `ADDI r0 r1 10`). Кодировки совпадают с Python `core.asm` (проверено на `ADD`/`ADDI`).

```bash
toolchain/llvm-build-e32c/bin/llvm-mc -triple=e32c-unknown-elf -show-encoding foo.s
```

Исходники бэкенда: `toolchain/llvm/E32C/` (TableGen из `docs/isa/opcodes.yaml` через `scripts/gen_llvm_e32c_td.py`).  
`llc`/ISel — урезанный порт с Lanai; для продакшн-компиляции C пока используйте Python-тулчейн выше.
