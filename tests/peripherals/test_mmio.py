"""MMIO GPIO, UART, timer + IRQ."""

from __future__ import annotations

from core import flags as F
from core.bus import MMIO_BASE_DEFAULT, SystemBus
from core.cycles import CycleCounter
from core.memory import Memory
from core.state import CPUState, SPR_IRQ_VECTOR


def test_gpio_bus_read_write() -> None:
    ram = Memory(4096)
    bus = SystemBus(ram)
    bus.set_cycle_counter(CycleCounter())
    addr = MMIO_BASE_DEFAULT
    bus.write_word(addr, 0xDEADBEEF)
    assert bus.read_word(addr) == 0xDEADBEEF
    assert bus.gpio.out == 0xDEADBEEF


def test_uart_tx_buffer() -> None:
    ram = Memory(256)
    bus = SystemBus(ram)
    bus.set_cycle_counter(CycleCounter())
    base = MMIO_BASE_DEFAULT + 0x1000
    bus.write_word(base + 0, 0x41)
    bus.write_word(base + 0, 0x42)
    assert bytes(bus.uart.tx_buffer) == b"AB"
    assert bus.read_word(base + 8) & 0x2  # TX idle


def test_uart_rx_queue() -> None:
    ram = Memory(256)
    bus = SystemBus(ram)
    bus.set_cycle_counter(CycleCounter())
    bus.uart.feed_rx(b"Z")
    base = MMIO_BASE_DEFAULT + 0x1000
    assert bus.read_word(base + 8) & 0x1
    assert bus.read_word(base + 4) & 0xFF == ord("Z")


def test_timer_irq_once_pending_blocks() -> None:
    ram = Memory(256)
    bus = SystemBus(ram)
    ctr = CycleCounter()
    bus.set_cycle_counter(ctr)
    st = CPUState()
    st.flags |= F.FLAG_INTENABLE
    st.spr_write(SPR_IRQ_VECTOR, 0x8000)

    tbase = MMIO_BASE_DEFAULT + 0x2000
    bus.write_word(tbase + 8, 2)
    bus.write_word(tbase + 12, 0)
    bus.write_word(tbase + 16, 1)

    ctr.add(2)
    bus.on_step_end(2, st, 0x100)
    assert st.pc == 0x8000
    assert st.spr_read(0) == 0x100
    assert bus.timer.read_reg(16) & 0x2

    st.set_pc(0x200)
    bus.on_step_end(3, st, 0x204)
    assert st.pc == 0x200

    bus.write_word(tbase + 16, 1 | 4)
    bus.on_step_end(5, st, 0x300)
    assert st.pc == 0x8000


def test_runner_counts_cycles_memory_only() -> None:
    from core.runner import Runner

    ram = Memory(256)
    st = CPUState()
    ram.write_word(0, 0x00000000)
    ram.write_word(4, 0xFFFFFFFF)
    r = Runner(st, ram)
    r.run(max_steps=10)
    assert st.halted
    assert r.cycle_counter.value == 2
