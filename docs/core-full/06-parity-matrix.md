# Матрица соответствия: Python full ↔ RTL `e32c_core`

**Эталон семантики:** `src/core/execute.py` + [ISA spec](../isa/spec.md) при `core_variant="full"`.

**RTL:** `test/src/core.sv` + `csr_spr.sv`.

Легенда: ✅ совпадает · ⚠️ частично · ❌ расхождение · — не применимо

## Идентификация и вариант


| Тема                | Python full  | RTL full               |
| ------------------- | ------------ | ---------------------- |
| CORE_INFO (SPR3)    | `0xE32C0100` | ✅                      |
| ISA_REVISION (SPR4) | `0x00010005` | ✅                      |
| FEATURES (SPR5)     | `0x0000000B` | ✅                      |
| Illegal opcodes     | нет          | ✅ (полный набор в RTL) |


## Регистры и PC


| Тема            | Python     | RTL           | Статус |
| --------------- | ---------- | ------------- | ------ |
| R0 read-as-zero | да         | да            | ✅      |
| R0 write ignore | да         | да            | ✅      |
| R31 = PC        | да         | `dbg_pc` only | ❌      |
| R30 ABI SP      | соглашение | соглашение    | ✅      |


**Рекомендация:** параметр `TIE_R31_TO_PC` или запись PC в `regs[31]` на каждом шаге для соответствия spec.

## Флаги и управление


| Тема              | Python        | RTL              | Статус                           |
| ----------------- | ------------- | ---------------- | -------------------------------- |
| ADDS/SUBS Z,C,V,S | spec          | реализовано      | ✅                                |
| ANDS S            | sign(result)  | `a[31]&b[31]`    | ❌                                |
| SUBI flags        | только Z      | только Z         | ⚠️ spec: «без флагов»            |
| Intenable storage | `flags` bit 0 | `int_enable` reg | ⚠️ эквивалентно, разное хранение |
| Intenable reset   | 0             | 1                | ❌                                |
| EI/DI             | flags         | int_enable       | ✅                                |


## Память


| Тема                | Python        | RTL         | Статус               |
| ------------------- | ------------- | ----------- | -------------------- |
| Aligned LDR/STR     | exception     | no check    | ❌                    |
| Byte mask LDR/STR   | 4 bytes used  | `ir[14:11]` | ⚠️ bit 4 mask unused |
| LDR mask==0         | skip bus read | still AR    | ⚠️                   |
| LDREX/STREX monitor | local         | local       | ✅                    |
| MMIO access         | SystemBus     | SoC fabric  | ✅ (в составе SoC)    |


## Умножение


| Mnemonic              | Python        | RTL               | Статус |
| --------------------- | ------------- | ----------------- | ------ |
| SMUL                  | да            | да                | ✅      |
| MUL/UMULL             | да            | да                | ✅      |
| SMULL                 | да            | да                | ✅      |
| MLA accumulator field | `res` [15:11] | `regs[ir[15:11]]` | ✅      |


## Ветвления и системные


| Тема                 | Python    | RTL                | Статус   |
| -------------------- | --------- | ------------------ | -------- |
| All branch ops       | да        | да                 | ✅        |
| NOP word 0           | legal     | illegal            | ❌        |
| HALT                 | да        | да                 | ✅        |
| Unknown opcode       | exception | illegal_instr+PC+4 | ❌ policy |
| illegal_instr sticky | N/A       | не сбрасывается    | ❌        |


## SPR / IRQ


| Тема                     | Python            | RTL                   | Статус    |
| ------------------------ | ----------------- | --------------------- | --------- |
| SPR index bits           | [15:11]           | [15:11]               | ✅         |
| RO SPR 3–5               | да                | да                    | ✅         |
| IRQ vector default       | 0 until write     | `0x100`               | ⚠️        |
| IRQ entry PC             | return after insn | `cur_pc` at fetch ack | ❌         |
| in_service block         | да                | да                    | ✅         |
| Timer IRQ line 0         | after step        | level in fetch        | ⚠️ timing |
| pending while in_service | false             | false                 | ✅         |


## Timing / cycles


| Тема            | Python                 | RTL             | Статус       |
| --------------- | ---------------------- | --------------- | ------------ |
| Pipeline        | none (1 step = 1 insn) | FSM multi-cycle | ⚠️ by design |
| cycles.py costs | abstract               | ≠ FSM cycles    | ⚠️           |
| MUL latency     | 3 (accounting)         | 1 EXEC + fetch  | ⚠️           |


## Покрытие верификации


| Механизм                      | Покрытие full ISA     |
| ----------------------------- | --------------------- |
| `tests/isa/test_vectors.yaml` | Python ✅              |
| `tb_core_isa`                 | RTL partial (nightly) |
| `compare_rtl_python`          | smoke only            |
| Formal parity                 | ❌ открыто             |


## Приоритет закрытия разрывов (для RTL full)


| P   | Item                                          | Effort     |
| --- | --------------------------------------------- | ---------- |
| P0  | NOP `ir==0` → PC+4, не illegal                | низкий     |
| P0  | ANDS sign = result[31]                        | низкий     |
| P1  | R31 ↔ PC (spec compliance)                    | средний    |
| P1  | Misalign trap или документировать AXI fault   | средний    |
| P1  | illegal_instr pulse / clear                   | низкий     |
| P2  | IRQ saved PC = PC+4 после прерванной insn     | средний    |
| P2  | int_enable reset 0                            | тривиально |
| P2  | Расширить compare_rtl_python / vectors на RTL | высокий    |


## TN9K и lite (справка)

Не входят в scope full, но для сравнения:


|           | full                     | tn9k RTL                                    | lite RTL     |
| --------- | ------------------------ | ------------------------------------------- | ------------ |
| CORE_INFO | `0xE32C0100`             | `0xE32C0110`                                | `0xE32C0120` |
| MUL       | ✅                        | illegal                                     | —            |
| LDREX     | ✅                        | illegal (FEATURES bit вводит в заблуждение) | —            |
| R31=PC    | Python да / RTL full нет | RTL да                                      | —            |


См. [profiles.md](../profiles.md).