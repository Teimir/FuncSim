"""Simulation control and UI-oriented state snapshots for the debugger GUI."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core import flags as F
from core.bus import SystemBus
from core.cycles import CycleCounter
from core.disasm import disassemble_word
from core.exceptions import BreakpointHit, CpuError, CpuHalted, IllegalInstruction, MisalignedAccess
from core.loader import load_binary, load_words, words_from_hex_lines
from core.memory import Memory
from core.runner import Runner
from core.state import CPUState, SPR_IRQ_VECTOR, SPR_SAVED_IRQ_PC
from core.trace import StepTrace

if TYPE_CHECKING:
    from core.mem_if import WordMemory


class StepKind(Enum):
    OK = "ok"
    HALTED_ALREADY = "halted_already"
    BREAKPOINT = "breakpoint"
    ERROR = "error"


@dataclass
class StepResult:
    kind: StepKind
    message: str | None = None
    steps_executed: int = 0


@dataclass
class ListingLine:
    addr: int
    word: int | None
    disasm: str
    is_pc: bool
    is_breakpoint: bool


@dataclass
class SdSnapshot:
    path: str | None
    mounted: bool
    lba: int
    status: int
    err_code: int
    sectors: int
    buffer_preview: str


@dataclass
class MmioSnapshot:
    mmio_base: int
    gpio_out: int
    uart_tx_hex: str
    uart_tx_ascii: str
    uart_status: int
    uart_rx_queue_len: int
    timer_counter_lo: int
    timer_counter_hi: int
    timer_compare_lo: int
    timer_compare_hi: int
    timer_ctrl: int
    sd: SdSnapshot


@dataclass
class UiSnapshot:
    regs: list[int]
    pc: int
    flags: int
    flag_ie: bool
    flag_z: bool
    flag_c: bool
    flag_v: bool
    flag_s: bool
    halted: bool
    spr_rows: list[tuple[int, int, str | None]]
    instruction_count: int
    cycles: int
    last_error: str | None
    fetch_addr: int
    fetch_word: int | None
    fetch_disasm: str
    listing: list[ListingLine]
    memory_rows: list[tuple[int, list[int | None]]]
    break_pcs: frozenset[int]
    mmio: MmioSnapshot | None
    trace: list[StepTrace]


def _spr_name(idx: int) -> str | None:
    if idx == SPR_SAVED_IRQ_PC:
        return "SAVED_IRQ_PC"
    if idx == SPR_IRQ_VECTOR:
        return "IRQ_VECTOR"
    return None


def _uart_tx_preview(uart: object, *, max_bytes: int = 64) -> tuple[str, str]:
    from core.peripherals.uart import Uart

    assert isinstance(uart, Uart)
    raw = bytes(uart.tx_buffer[-max_bytes:])
    hx = raw.hex(" ")
    ascii_s = "".join(chr(b) if 32 <= b < 127 else "." for b in raw)
    return hx, ascii_s


def _mmio_snapshot(bus: SystemBus) -> MmioSnapshot:
    base = bus.mmio_base
    uart = bus.uart
    hx, asc = _uart_tx_preview(uart)
    st = uart.read_reg(uart.UART_STATUS)
    t = bus.timer
    sd_info = bus.sd.snapshot_info()
    sd_snap = SdSnapshot(
        path=sd_info["path"],  # type: ignore[arg-type]
        mounted=bool(sd_info["mounted"]),
        lba=int(sd_info["lba_reg"]),
        status=int(sd_info["status"]),
        err_code=int(sd_info["err_code"]),
        sectors=int(sd_info["sectors"]),
        buffer_preview=str(sd_info["buffer_preview"]),
    )
    return MmioSnapshot(
        mmio_base=base,
        gpio_out=bus.gpio.out,
        uart_tx_hex=hx,
        uart_tx_ascii=asc,
        uart_status=st,
        uart_rx_queue_len=uart.rx_queued,
        timer_counter_lo=t.read_reg(0),
        timer_counter_hi=t.read_reg(4),
        timer_compare_lo=t.read_reg(8),
        timer_compare_hi=t.read_reg(12),
        timer_ctrl=t.read_reg(16),
        sd=sd_snap,
    )


@dataclass
class DebugController:
    """Owns CPUState, memory bus, Runner; exposes snapshot and stepping for GUI."""

    state: CPUState
    mem: WordMemory
    runner: Runner
    load_addr: int = 0
    instruction_count: int = 0
    last_error: str | None = None
    trace_max: int = 500
    listing_radius: int = 16
    mem_page_lines: int = 16
    mem_words_per_line: int = 4
    _mem_page_base: int = 0
    _trace: deque[StepTrace] = field(default_factory=lambda: deque(maxlen=500))

    def __post_init__(self) -> None:
        object.__setattr__(self, "_trace", deque(maxlen=self.trace_max))

    def _append_trace(self, tr: StepTrace) -> None:
        self._trace.append(tr)

    @classmethod
    def create(
        cls,
        *,
        ram: Memory,
        use_mmio: bool = False,
        mmio_base: int | None = None,
        load_addr: int = 0,
        uart: object | None = None,
        sd_image: Path | None = None,
        sd_create_sectors: int | None = None,
    ) -> DebugController:
        from core.bus import MMIO_BASE_DEFAULT

        st = CPUState()
        if use_mmio:
            from core.peripherals.uart import Uart

            u = uart if uart is not None else Uart()
            base = MMIO_BASE_DEFAULT if mmio_base is None else mmio_base
            mem = SystemBus(
                ram,
                mmio_base=base,
                uart=u,
                sd_image=sd_image,
                sd_create_sectors=sd_create_sectors,
            )
        else:
            mem = ram
        cycle_counter = CycleCounter()
        ctrl = cls(state=st, mem=mem, runner=Runner(st, mem, cycle_counter=cycle_counter), load_addr=load_addr)
        ctrl.runner.on_step = ctrl._append_trace
        st.set_pc(load_addr)
        return ctrl

    @property
    def mem_page_base(self) -> int:
        return self._mem_page_base

    @mem_page_base.setter
    def mem_page_base(self, value: int) -> None:
        self._mem_page_base = value & 0xFFFFFFFF

    def load_binary_file(self, path: Path, base: int | None = None) -> None:
        addr = self.load_addr if base is None else base
        load_binary(self.mem, addr, path)
        self.load_addr = addr

    def load_hex_file(self, path: Path, base: int | None = None) -> None:
        addr = self.load_addr if base is None else base
        ws = words_from_hex_lines(path.read_text(encoding="utf-8"))
        load_words(self.mem, addr, ws)
        self.load_addr = addr

    def reset_cpu(self, *, preserve_breakpoints: bool = True) -> None:
        breaks = set(self.runner.break_pcs) if preserve_breakpoints else set()
        self.state.regs = [0] * 32
        self.state.flags = 0
        self.state.halted = False
        self.state.spr = {}
        self.state.set_pc(self.load_addr)
        self.runner.cycle_counter.reset()
        self.instruction_count = 0
        self.last_error = None
        self.runner.break_pcs = breaks
        self._trace.clear()

    def step(self) -> StepResult:
        try:
            self.runner.step()
        except CpuHalted as e:
            msg = str(e)
            return StepResult(StepKind.HALTED_ALREADY, msg)
        except BreakpointHit as e:
            self.last_error = None
            return StepResult(StepKind.BREAKPOINT, f"breakpoint at 0x{e.pc:x}")
        except (IllegalInstruction, MisalignedAccess, CpuError, IndexError) as e:
            self.last_error = str(e)
            return StepResult(StepKind.ERROR, str(e))
        except Exception as e:  # noqa: BLE001
            self.last_error = repr(e)
            return StepResult(StepKind.ERROR, repr(e))
        self.instruction_count += 1
        self.last_error = None
        return StepResult(StepKind.OK)

    def run_n(self, n: int) -> StepResult:
        if n < 1:
            return StepResult(StepKind.OK, steps_executed=0)
        done = 0
        while done < n:
            if self.state.halted:
                self.last_error = None
                return StepResult(StepKind.OK, "CPU halted", steps_executed=done)
            r = self.step()
            done += 1
            if r.kind == StepKind.HALTED_ALREADY:
                return StepResult(StepKind.HALTED_ALREADY, r.message, steps_executed=done)
            if r.kind == StepKind.BREAKPOINT:
                return StepResult(StepKind.BREAKPOINT, r.message, steps_executed=done)
            if r.kind == StepKind.ERROR:
                return StepResult(StepKind.ERROR, r.message, steps_executed=done)
        self.last_error = None
        return StepResult(StepKind.OK, steps_executed=done)

    def clear_trace(self) -> None:
        self._trace.clear()

    def feed_uart_rx(self, data: bytes) -> None:
        if isinstance(self.mem, SystemBus):
            self.mem.uart.feed_rx(data)

    def attach_sd_image(self, path: Path, *, create_sectors: int | None = None) -> None:
        if not isinstance(self.mem, SystemBus):
            raise TypeError("MMIO bus required for SD")
        self.mem.sd.mount(path, create_sectors=create_sectors)

    def detach_sd_image(self) -> None:
        if isinstance(self.mem, SystemBus):
            self.mem.sd.unmount()

    def write_ram_word(self, addr: int, value: int) -> None:
        """Write a word only to backing RAM (not MMIO). Address must be word-aligned and in range."""
        if addr % 4 != 0:
            raise ValueError("address must be word-aligned")
        v = value & 0xFFFFFFFF
        sz = self.ram_size()
        if not (0 <= addr < sz):
            raise ValueError(f"address 0x{addr:x} not in RAM [0, 0x{sz:x})")
        if isinstance(self.mem, SystemBus):
            self.mem.ram.write_word(addr, v)
        elif isinstance(self.mem, Memory):
            self.mem.write_word(addr, v)
        else:
            raise TypeError("unsupported memory backend")

    def set_gpr(self, index: int, value: int) -> None:
        """Set GPR; R0 ignored; PC (R31) must stay word-aligned."""
        if index == 0:
            return
        v = value & 0xFFFFFFFF
        if index == 31 and v % 4 != 0:
            raise ValueError("PC (R31) must be word-aligned")
        self.state.reg_write(index, v)

    def export_snapshot_dict(self) -> dict[str, Any]:
        """JSON-friendly debug snapshot (regs, listing, trace, breakpoints, MMIO summary)."""
        s = self.snapshot()
        listing = [
            {
                "addr": f"0x{ln.addr:08x}",
                "word": None if ln.word is None else f"0x{ln.word:08x}",
                "disasm": ln.disasm,
                "is_pc": ln.is_pc,
                "is_breakpoint": ln.is_breakpoint,
            }
            for ln in s.listing
        ]
        trace = [asdict(t) for t in s.trace]
        mmio_d: dict[str, Any] | None = asdict(s.mmio) if s.mmio is not None else None
        return {
            "regs": [f"0x{x:08x}" for x in s.regs],
            "pc": f"0x{s.pc:08x}",
            "flags": f"0x{s.flags:08x}",
            "flag_bits": {
                "IE": s.flag_ie,
                "Z": s.flag_z,
                "C": s.flag_c,
                "V": s.flag_v,
                "S": s.flag_s,
            },
            "halted": s.halted,
            "spr": [{"idx": i, "value": f"0x{v:08x}", "name": n} for i, v, n in s.spr_rows],
            "instruction_count": s.instruction_count,
            "cycles": s.cycles,
            "last_error": s.last_error,
            "fetch": {
                "addr": f"0x{s.fetch_addr:08x}",
                "word": None if s.fetch_word is None else f"0x{s.fetch_word:08x}",
                "disasm": s.fetch_disasm,
            },
            "listing": listing,
            "memory_page_base": f"0x{self._mem_page_base:08x}",
            "breakpoints": sorted(f"0x{a:08x}" for a in s.break_pcs),
            "mmio": mmio_d,
            "trace": trace,
        }

    def ram_size(self) -> int:
        if isinstance(self.mem, SystemBus):
            return self.mem.ram_size
        if isinstance(self.mem, Memory):
            return self.mem.size
        return 0

    def _read_word_safe(self, addr: int) -> tuple[int | None, str]:
        try:
            return self.mem.read_word(addr), ""
        except Exception as e:  # noqa: BLE001
            return None, str(e)

    def _build_listing(self, pc: int) -> list[ListingLine]:
        r = self.listing_radius
        start = (pc - r * 4) & 0xFFFFFFFF
        start = start - (start % 4)
        lines: list[ListingLine] = []
        br = self.runner.break_pcs
        for i in range(2 * r + 1):
            addr = (start + i * 4) & 0xFFFFFFFF
            w, err = self._read_word_safe(addr)
            if w is None:
                dis = f"<{err}>"
            else:
                dis = disassemble_word(w)
            lines.append(
                ListingLine(
                    addr=addr,
                    word=w,
                    disasm=dis,
                    is_pc=(addr == pc),
                    is_breakpoint=(addr in br),
                )
            )
        return lines

    def _build_memory_rows(self, page_base: int) -> list[tuple[int, list[int | None]]]:
        base = page_base - (page_base % 4)
        rows: list[tuple[int, list[int | None]]] = []
        for line in range(self.mem_page_lines):
            row_addr = (base + line * self.mem_words_per_line * 4) & 0xFFFFFFFF
            words: list[int | None] = []
            for w in range(self.mem_words_per_line):
                a = (row_addr + w * 4) & 0xFFFFFFFF
                try:
                    words.append(self.mem.read_word(a))
                except Exception:  # noqa: BLE001
                    words.append(None)
            rows.append((row_addr, words))
        return rows

    def snapshot(self) -> UiSnapshot:
        pc = self.state.pc
        fl = self.state.flags
        fetch_w, fetch_err = self._read_word_safe(pc)
        if fetch_w is None:
            fetch_dis = f"<{fetch_err}>"
        else:
            fetch_dis = disassemble_word(fetch_w)

        spr_rows = sorted((k, v & 0xFFFFFFFF, _spr_name(k)) for k, v in self.state.spr.items())

        mmio_snap: MmioSnapshot | None = None
        if isinstance(self.mem, SystemBus):
            mmio_snap = _mmio_snapshot(self.mem)

        page = self._mem_page_base
        if page % 4:
            page -= page % 4

        return UiSnapshot(
            regs=[self.state.reg_read(i) for i in range(32)],
            pc=pc,
            flags=fl,
            flag_ie=bool(fl & F.FLAG_INTENABLE),
            flag_z=bool(fl & F.FLAG_ZERO),
            flag_c=bool(fl & F.FLAG_CARRY),
            flag_v=bool(fl & F.FLAG_OVERFLOW),
            flag_s=bool(fl & F.FLAG_SIGN),
            halted=self.state.halted,
            spr_rows=spr_rows,
            instruction_count=self.instruction_count,
            cycles=self.runner.cycle_counter.value,
            last_error=self.last_error,
            fetch_addr=pc,
            fetch_word=fetch_w,
            fetch_disasm=fetch_dis,
            listing=self._build_listing(pc),
            memory_rows=self._build_memory_rows(page),
            break_pcs=frozenset(self.runner.break_pcs),
            mmio=mmio_snap,
            trace=list(self._trace),
        )
