# 08 — Ассемблер и образы программ

Модуль: `src/core/asm.py`, CLI: `python -m cli.asm`.

## Синтаксис строки

- Одна инструкция на строку (или псевдо PUSH/POP).
- Комментарий: `#` до конца строки.
- Метки: `name:` в начале строки.
- Константы: `.equ NAME value`.

## cli.asm

```bash
python -m cli.asm examples/boot_smoke.asm -o /tmp/boot.hex
python -m cli.asm docs/tutorial/asm/lab_fundamentals.asm
```

Без `-o` — hex-слова на stdout.

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
| BEQ label | BJ 0, PC-relative via r31 |
| B label | JMP PC-relative |
| PUSH r | SUBI 30 30 4; STRPOST 30 r 15 0 |
| POP r | LDRPOST 30 r 15 0; ADDI 30 30 4 |

## Типичные ошибки

| Сообщение | Причина |
|-----------|---------|
| `unknown mnemonic` | Опечатка или инструкция не в opcodes.yaml |
| `imm11 out of range` | Смещение ветки > ±1023 слов |
| `MisalignedAccess` | LDR/STR по нечётному адресу |
| `assemble error` | Неверное число операндов |

## Все labs ISA

```bash
for f in docs/tutorial/asm/lab_*.asm; do
  echo "=== $f ==="
  python -m cli.sim --asm "$f" --until-halt --max-steps 10000
done
```

PowerShell:

```powershell
Get-ChildItem docs\tutorial\asm\lab_*.asm | ForEach-Object {
  python -m cli.sim --asm $_.FullName --until-halt
}
```

## Дальше

[11-cli-simulator.md](11-cli-simulator.md) — полный CLI прогона.
