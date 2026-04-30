#!/usr/bin/env python3
"""UART calculator demo on the E32C simulator.

Expression format: <number><op><number>\n, for example: 12*34\n
Supported operators: +, -, *
Result is printed as decimal (up to 32-bit unsigned). Invalid expressions return '?'.
Command `HALT\n` stops calculator loop.

Run from repo root:
  python examples/uart_calculator.py
  python examples/uart_calculator.py "7*8\n"
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.asm import assemble_line
from core.bus import SystemBus
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState

POOL = 0x100
MAIN = 0x200


def _assemble_with_labels(lines: list[str], base_addr: int) -> list[int]:
    labels: dict[str, int] = {}
    pc = base_addr
    for raw in lines:
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        if s.startswith(":"):
            labels[s[1:]] = pc
            continue
        pc += 4

    out: list[int] = []
    pc = base_addr
    for raw in lines:
        s = raw.split("#", 1)[0].strip()
        if not s or s.startswith(":"):
            continue
        parts = s.split()
        if parts[0] in {"JMP", "JZ", "JNZ", "JC", "JS", "JO"} and len(parts) == 3 and parts[2].startswith("@"):
            label = parts[2][1:]
            if label not in labels:
                raise ValueError(f"unknown label: {label}")
            imm = labels[label] - pc
            parts[2] = str(imm)
            s = " ".join(parts)
        out.append(assemble_line(s))
        pc += 4
    return out


def _build_calc_program() -> list[int]:
    lines = [
        "ADDI 0 20 256",  # pool base
        "LDR 20 21 15 0",  # mmio base (0xffff0000)
        "ADDI 21 29 4096",  # uart base (mmio + 0x1000)
        "LDR 20 22 15 4",  # '0'
        "LDR 20 23 15 8",  # '+'
        "LDR 20 24 15 12",  # '-'
        "LDR 20 25 15 16",  # '*'
        "LDR 20 26 15 20",  # '\n'
        "ADDI 0 27 1",  # UART status FLAG_RX_READY
        "LDR 20 28 15 24",  # '?'
        "ADDI 0 16 10",  # const 10
        "LDR 20 30 15 28",  # 1000000000
        "LDR 20 17 15 64",  # 'H'
        "LDR 20 18 15 68",  # 'A'
        "LDR 20 19 15 72",  # 'L'
        "LDR 20 12 15 76",  # 'T'
        ":main_loop",
        "ADDI 0 1 0",  # a = 0
        "ADDI 0 2 0",  # op = 0
        "ADDI 0 3 0",  # b = 0
        "ADDI 0 13 0",  # seen_a = 0
        "ADDI 0 14 0",  # seen_b = 0
        "ADDI 0 15 0",  # printed = 0
        ":read_a_wait",
        "LDR 29 10 1 8",  # UART status
        "AND 10 27 10",
        "SUBS 10 27 11",
        "JNZ 31 @read_a_wait",
        "LDR 29 6 1 4",  # ch
        "SUBS 13 0 11",
        "JNZ 31 @check_ops",
        "SUBS 6 17 11",
        "JZ 31 @halt_cmd_a",
        ":check_ops",
        "SUBS 6 23 11",
        "JZ 31 @op_plus",
        "SUBS 6 24 11",
        "JZ 31 @op_minus",
        "SUBS 6 25 11",
        "JZ 31 @op_mul",
        "SUBS 6 22 8",  # digit = ch - '0'
        "JS 31 @bad",
        "SUBS 8 16 11",
        "JS 31 @a_digit_ok",  # digit < 10
        "JMP 31 @bad",
        ":a_digit_ok",
        "MUL 1 16 1 5",
        "SUBS 5 0 11",
        "JNZ 31 @bad",
        "ADD 1 8 1",
        "ADDI 0 13 1",
        "JMP 31 @read_a_wait",
        ":op_plus",
        "SUBS 13 0 11",
        "JZ 31 @bad",
        "ADDI 0 2 43",
        "JMP 31 @read_b_wait",
        ":op_minus",
        "SUBS 13 0 11",
        "JZ 31 @bad",
        "ADDI 0 2 45",
        "JMP 31 @read_b_wait",
        ":op_mul",
        "SUBS 13 0 11",
        "JZ 31 @bad",
        "ADDI 0 2 42",
        "JMP 31 @read_b_wait",
        ":read_b_wait",
        "LDR 29 10 1 8",
        "AND 10 27 10",
        "SUBS 10 27 11",
        "JNZ 31 @read_b_wait",
        "LDR 29 6 1 4",  # ch
        "SUBS 6 26 11",  # newline?
        "JZ 31 @compute",
        "SUBS 6 22 8",  # digit = ch - '0'
        "JS 31 @bad",
        "SUBS 8 16 11",
        "JS 31 @b_digit_ok",
        "JMP 31 @bad",
        ":b_digit_ok",
        "MUL 3 16 3 5",
        "SUBS 5 0 11",
        "JNZ 31 @bad",
        "ADD 3 8 3",
        "ADDI 0 14 1",
        "JMP 31 @read_b_wait",
        ":halt_cmd_a",
        ":halt_wait_1",
        "LDR 29 10 1 8",
        "AND 10 27 10",
        "SUBS 10 27 11",
        "JNZ 31 @halt_wait_1",
        "LDR 29 6 1 4",
        "SUBS 6 18 11",
        "JNZ 31 @bad",
        ":halt_wait_2",
        "LDR 29 10 1 8",
        "AND 10 27 10",
        "SUBS 10 27 11",
        "JNZ 31 @halt_wait_2",
        "LDR 29 6 1 4",
        "SUBS 6 19 11",
        "JNZ 31 @bad",
        ":halt_wait_3",
        "LDR 29 10 1 8",
        "AND 10 27 10",
        "SUBS 10 27 11",
        "JNZ 31 @halt_wait_3",
        "LDR 29 6 1 4",
        "SUBS 6 12 11",
        "JNZ 31 @bad",
        ":halt_wait_4",
        "LDR 29 10 1 8",
        "AND 10 27 10",
        "SUBS 10 27 11",
        "JNZ 31 @halt_wait_4",
        "LDR 29 6 1 4",
        "SUBS 6 26 11",
        "JNZ 31 @bad",
        "HALT",
        ":compute",
        "SUBS 14 0 11",
        "JZ 31 @bad",
        "SUBS 2 23 11",  # '+'
        "JZ 31 @do_add",
        "SUBS 2 24 11",  # '-'
        "JZ 31 @do_sub",
        "SUBS 2 25 11",  # '*'
        "JZ 31 @do_mul",
        "JMP 31 @bad",
        ":do_add",
        "ADD 1 3 4",
        "JMP 31 @print_number",
        ":do_sub",
        "SUBS 1 3 4",
        "JS 31 @bad",  # negative
        "JMP 31 @print_number",
        ":do_mul",
        "MUL 1 3 4 5",
        "SUBS 5 0 11",
        "JNZ 31 @bad",
        ":print_number",
        "ADDI 0 15 0",  # printed = 0
        "LDR 20 7 15 28",  # place = 1000000000
        "JMP 31 @print_place",
        ":next_1e8",
        "LDR 20 7 15 32",  # place = 100000000
        "JMP 31 @print_place",
        ":next_1e7",
        "LDR 20 7 15 36",  # place = 10000000
        "JMP 31 @print_place",
        ":next_1e6",
        "LDR 20 7 15 40",  # place = 1000000
        "JMP 31 @print_place",
        ":next_1e5",
        "LDR 20 7 15 44",  # place = 100000
        "JMP 31 @print_place",
        ":next_1e4",
        "LDR 20 7 15 48",  # place = 10000
        "JMP 31 @print_place",
        ":next_1e3",
        "LDR 20 7 15 52",  # place = 1000
        "JMP 31 @print_place",
        ":next_1e2",
        "LDR 20 7 15 56",  # place = 100
        "JMP 31 @print_place",
        ":next_1e1",
        "LDR 20 7 15 60",  # place = 10
        "JMP 31 @print_place",
        ":print_ones",
        "ADDI 4 6 48",
        "STR 29 6 1 0",
        "STR 29 26 1 0",  # '\n'
        "JMP 31 @main_loop",
        ":print_place",
        "ADDI 0 6 0",  # digit = 0
        ":print_place_loop",
        "SUBS 4 7 11",
        "JS 31 @print_place_done",
        "SUB 4 7 4",
        "ADDI 6 6 1",
        "JMP 31 @print_place_loop",
        ":print_place_done",
        "SUBS 15 0 11",
        "JNZ 31 @emit_place_digit",
        "SUBS 6 0 11",
        "JZ 31 @advance_place",
        ":emit_place_digit",
        "ADDI 6 6 48",
        "STR 29 6 1 0",
        "ADDI 0 15 1",
        ":advance_place",
        "SUBS 7 30 11",
        "JZ 31 @next_1e8",
        "LDR 20 6 15 32",  # compare with 100000000
        "SUBS 7 6 11",
        "JZ 31 @next_1e7",
        "LDR 20 6 15 36",  # compare with 10000000
        "SUBS 7 6 11",
        "JZ 31 @next_1e6",
        "LDR 20 6 15 40",  # compare with 1000000
        "SUBS 7 6 11",
        "JZ 31 @next_1e5",
        "LDR 20 6 15 44",  # compare with 100000
        "SUBS 7 6 11",
        "JZ 31 @next_1e4",
        "LDR 20 6 15 48",  # compare with 10000
        "SUBS 7 6 11",
        "JZ 31 @next_1e3",
        "LDR 20 6 15 52",  # compare with 1000
        "SUBS 7 6 11",
        "JZ 31 @next_1e2",
        "LDR 20 6 15 56",  # compare with 100
        "SUBS 7 6 11",
        "JZ 31 @next_1e1",
        "LDR 20 6 15 60",  # compare with 10
        "SUBS 7 6 11",
        "JZ 31 @print_ones",
        "JMP 31 @print_ones",
        ":bad",
        "STR 29 28 1 0",  # '?'
        "STR 29 26 1 0",
        "JMP 31 @main_loop",
    ]
    return _assemble_with_labels(lines, MAIN)


def prepare_uart_calculator(ram: Memory, bus: SystemBus, st: CPUState) -> None:
    """Load UART calculator program and constants into memory."""
    ram.write_word(POOL + 0x00, 0xFFFF_0000)
    ram.write_word(POOL + 0x04, ord("0"))
    ram.write_word(POOL + 0x08, ord("+"))
    ram.write_word(POOL + 0x0C, ord("-"))
    ram.write_word(POOL + 0x10, ord("*"))
    ram.write_word(POOL + 0x14, ord("\n"))
    ram.write_word(POOL + 0x18, ord("?"))
    ram.write_word(POOL + 0x1C, 1000000000)
    ram.write_word(POOL + 0x20, 100000000)
    ram.write_word(POOL + 0x24, 10000000)
    ram.write_word(POOL + 0x28, 1000000)
    ram.write_word(POOL + 0x2C, 100000)
    ram.write_word(POOL + 0x30, 10000)
    ram.write_word(POOL + 0x34, 1000)
    ram.write_word(POOL + 0x38, 100)
    ram.write_word(POOL + 0x3C, 10)
    ram.write_word(POOL + 0x40, ord("H"))
    ram.write_word(POOL + 0x44, ord("A"))
    ram.write_word(POOL + 0x48, ord("L"))
    ram.write_word(POOL + 0x4C, ord("T"))

    words = _build_calc_program()
    addr = MAIN
    for w in words:
        ram.write_word(addr, w)
        addr += 4
    st.set_pc(MAIN)


def run_expr(expr: bytes) -> tuple[bytes, int, int, int]:
    ram = Memory(1 << 20)
    bus = SystemBus(ram)
    st = CPUState()
    prepare_uart_calculator(ram, bus, st)
    start_tx_len = len(bus.uart.tx_buffer)
    bus.uart.feed_rx(expr)
    runner = Runner(st, bus)
    steps = 0
    max_steps = 100_000
    t0_ns = time.perf_counter_ns()
    while steps < max_steps:
        if st.halted:
            elapsed_ns = time.perf_counter_ns() - t0_ns
            return bytes(bus.uart.tx_buffer[start_tx_len:]), steps, runner.cycle_counter.value, elapsed_ns
        runner.step()
        steps += 1
        out = bytes(bus.uart.tx_buffer[start_tx_len:])
        nl = out.find(b"\n")
        if nl >= 0:
            elapsed_ns = time.perf_counter_ns() - t0_ns
            return out[: nl + 1], steps, runner.cycle_counter.value, elapsed_ns
    raise RuntimeError(f"no response within step budget; steps={steps}")


def main() -> None:
    expr = (sys.argv[1] if len(sys.argv) > 1 else "7+2\n").encode("latin-1", errors="replace")
    out, steps, cycles, elapsed_ns = run_expr(expr)
    elapsed_ms = elapsed_ns / 1_000_000.0
    ips = (steps * 1_000_000_000.0 / elapsed_ns) if elapsed_ns > 0 else 0.0
    cps = (cycles * 1_000_000_000.0 / elapsed_ns) if elapsed_ns > 0 else 0.0
    print("=== uart_calculator ===")
    print(f"RX: {expr!r}")
    print(f"TX: {out!r}")
    print(f"steps={steps} | cycles={cycles} | wall_ms={elapsed_ms:.3f} | kIPS={ips/1000.0:.2f} | kCPS={cps/1000.0:.2f}")
    print(out.decode("latin-1", errors="replace"), end="")


if __name__ == "__main__":
    main()
