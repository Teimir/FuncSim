# 08 — Ассемблер и образы программ

Пакет: `src/core/asm/`, CLI: `python -m cli.asm` или `e32c-asm`.

## Синтаксис строки

- Одна инструкция на строку (или псевдо PUSH/POP).
- Комментарий: `#` до конца строки.
- Метки: `name:` в начале строки.
- Регистры: `r0`…`r31` или числа `0`…`31`.
- Константы: `.equ NAME expr` (выражения: `+ - * & | << >>`, скобки).

## Директивы

| Директива | Назначение |
|-----------|------------|
| `.include "path.asm"` | Вставить файл (путь относительно текущего) |
| `.org addr` | Установить адрес (байты) |
| `.align [n]` | Выровнять LC (по умолчанию 4) |
| `.word expr …` | Положить 32-bit слова |
| `.skip nbytes [, fill]` | Пропуск байт |
| `.macro name args…` / `.endm` | Макрос; параметры `{name}` или `name=default` |

## cli.asm

```bash
python -m cli.asm examples/boot_smoke.asm -o /tmp/boot.hex
python -m cli.asm examples/blink_uart_irq_main.asm --link handler.asm@0x100 -o fw.hex
python -m cli.asm examples/boot_smoke.asm -l listing.lst
e32c-asm examples/boot_smoke.asm --format bin -o boot.bin
```

Без `-o` — hex-слова на stdout (`0x........` по строке).

## Линковка (main + handler)

```bash
python -m cli.asm main.asm --link handler.asm@0x100 -o firmware.hex
```

То же делает `scripts/gen_firmware_hex.py --asm main.asm --handler handler.asm --handler-addr 0x100`.

## Длинные переходы

Если метка дальше ±1023 байт от ветки, ассемблер вставляет long-branch (загрузка адреса в **r14**, затем `JMP r14, 0`). Не используйте **r14** в том же блоке без сохранения.

## Загрузка в симулятор

| Источник | Флаг | Примечание |
|----------|------|------------|
| asm | `--asm path` | Сборка на лету |
| hex | `--hex path` | Одно 32-bit слово на строку |
| bin | `--bin path` | LE байты |

```bash
python -m cli.sim --hex examples/smoke.hex --load-addr 0 --until-halt
python -m cli.sim --asm docs/tutorial/asm/lab_alu.asm --load-addr 0x1000 --until-halt
```

## Псевдоинструкции

| Псевдо | Развёртка |
|--------|-----------|
| MOV dst imm | ADDI 0 dst imm |
| CMP r1 r2 | SUBS r1 r2 0 |
| CMN r1 r2 | ADDS r1 r2 0 |
| TST r1 r2 | ANDS r1 r2 0 |
| BEQ label | PC-relative через r31 (IP) |
| B label | JMP PC-relative |
| JMP label | JMP r31, offset |
| PUSH r | SUBI 30 30 4; STRPOST 30 r 15 0 |
| POP r | LDRPOST 30 r 15 0; ADDI 30 30 4 |

## Типичные ошибки

| Сообщение | Причина |
|-----------|---------|
| `unknown mnemonic` | Опечатка или инструкция не в opcodes.yaml |
| `imm11 out of range` | Смещение ветки > ±1023 байт без long-branch |
| `undefined label` | Метка не объявлена |
| `assemble error` | Неверное число операндов |

## Дальше

[11-cli-simulator.md](11-cli-simulator.md) — полный CLI прогона.
