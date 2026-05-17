# RTL full: текущая реализация (`e32c_core`)

Файл: [`test/src/core.sv`](../../test/src/core.sv).  
SPR: [`test/src/csr_spr.sv`](../../test/src/csr_spr.sv).  
Умножение: [`test/src/mul_dsp.sv`](../../test/src/mul_dsp.sv).

## Параметры и константы

```systemverilog
`include "cores_generated.svh"
// csr_spr: E32C_CORE_INFO_FULL, E32C_ISA_REVISION, E32C_FEATURES_FULL
```

## Реализованные группы ISA

| Группа | Статус | Примечание |
|--------|--------|------------|
| LDR/STR + mask | да | 4-bit mask `ir[14:11]` |
| LDRPRE/POST, STRPRE/POST | да | mem_* metadata в FSM |
| LDREX/STREX | да | local monitor |
| SMUL, MUL, UMULL, SMULL, MLA | да | комментарии «NOP» устарели |
| ADD..XOR, shifts, ROL/ROR | да | |
| ADDI/SUBI, ADDS/SUBS, ADCSI/SUBSI | да | |
| ADC/ADCS, SBC/SBCS, ANDS | да | ANDS sf — см. parity |
| BIC, MVN, NEG | да | |
| JMP, JZ, JNZ, JC, JS, JO, BJ | да | |
| EI, DI, READSPR, WRITESPR, IRET | да | SPR [15:11] |
| HALT | да | `ir == 32'hFFFF_FFFF` |
| NOP (`ir==0`) | **нет** | → illegal, PC+4 |

## FSM (см. [03-microarchitecture.md](03-microarchitecture.md))

Состояния `ST_FETCH_REQ` … `ST_MEM_WR_WAIT` (7 состояний).

### Fetch

- `if_req_addr` = `dbg_pc`, кроме IRQ redirect на `irq_vector`.
- `ir` латчится в `ST_FETCH_WAIT`.
- `if_stall` блокирует выход из FETCH_REQ.

### Execute highlights

- **Multiply:** `e32c_mul_u_dsp`, `e32c_mul_s_dsp` — произведение за один EXEC.
- **READSPR:** `csr_rd_idx_eff = ir[15:11]` в EXEC (same-cycle read).
- **IRET:** `dbg_pc <= saved_irq_pc` из `csr_spr`.
- **Branches:** обновление `dbg_pc` и `if_req_addr`.

### Memory

- Split-phase AXI; writeback в MEM_RD_WAIT.
- STREX: success path через MEM_WR; fail — status 1 в regs, без store.

## Регистры и PC

| Элемент | Реализация |
|---------|------------|
| PC | `dbg_pc` (отдельно от `regs[31]`) |
| GPR | `regs[0:31]`, R0 read 0 в ALU paths |
| Flags | `zf`, `cf`, `vf`, `sf` |
| Intenable | `int_enable` reg (не flags[0]) |
| Exclusive | `exclusive_addr`, `exclusive_valid` |

## Порты отладки

| Порт | Назначение |
|------|------------|
| `dbg_pc` | PC observation |
| `dbg_halted` | HALT state |
| `illegal_instr` | выход illegal (sticky) |
| `dbg_r1`..`dbg_r4` | снимок GPR |

## Подключение в SoC

[`top.sv`](../../test/src/top.sv):

```systemverilog
e32c_core u_core ( ... );  // when !USE_TN9K_CORE && !USE_LITE_CORE
```

- I-cache / boot ROM / external AXI для IF.
- D-port → crossbar → RAM + APB.

## Тесты RTL

| Bench | Покрытие |
|-------|----------|
| `tb_core_isa` | расширенный ISA (nightly `--full`) |
| `tb_core_irq` | IRQ flow |
| `compare_rtl_python` | smoke cosim |
| `tb_core_tn9k_smoke` | **не** full (TN9K) |

## Известные ограничения текущего RTL

1. Слово `0x00000000` — illegal, не NOP.
2. `illegal_instr` не сбрасывается автоматически.
3. `ANDS` Sign flag ≠ Python/spec intent.
4. `int_enable` reset = 1.
5. Нет проверки misaligned EA на AXI.
6. LDR с mask=0 всё равно идёт в память.
7. IRQ saved PC = fetch PC, не «после инструкции» как Python timer.

Целевые исправления: [06-parity-matrix.md](06-parity-matrix.md).
