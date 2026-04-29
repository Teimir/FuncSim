from core.debug_controller import DebugController, StepKind
from core.memory import Memory


def test_reset_and_step_nop() -> None:
    ram = Memory(1 << 16)
    ctrl = DebugController.create(ram=ram, load_addr=0x1000)
    ram.write_word(0x1000, 0)
    ctrl.state.set_pc(0x1000)
    r = ctrl.step()
    assert r.kind == StepKind.OK
    assert ctrl.state.pc == 0x1004
    assert ctrl.instruction_count == 1


def test_snapshot_regs_and_listing() -> None:
    ram = Memory(1 << 16)
    ctrl = DebugController.create(ram=ram, load_addr=0)
    ram.write_word(0, 0x84221800)
    ctrl.state.reg_write(1, 3)
    ctrl.state.reg_write(2, 4)
    snap = ctrl.snapshot()
    assert snap.regs[1] == 3
    assert snap.fetch_disasm.startswith("ADD")
    assert any(ln.is_pc for ln in snap.listing)


def test_breakpoint_before_instruction() -> None:
    ram = Memory(1 << 16)
    ctrl = DebugController.create(ram=ram, load_addr=0x2000)
    ctrl.runner.break_pcs.add(0x2000)
    ctrl.state.set_pc(0x2000)
    r = ctrl.step()
    assert r.kind == StepKind.BREAKPOINT
    assert ctrl.instruction_count == 0


def test_write_ram_word() -> None:
    ram = Memory(1 << 16)
    ctrl = DebugController.create(ram=ram, load_addr=0)
    ctrl.write_ram_word(0x10, 0xDEADBEEF)
    assert ram.read_word(0x10) == 0xDEADBEEF


def test_export_snapshot_json_roundtrip() -> None:
    import json

    ram = Memory(1 << 16)
    ctrl = DebugController.create(ram=ram, load_addr=0)
    ctrl.state.reg_write(1, 0x42)
    d = ctrl.export_snapshot_dict()
    json.dumps(d)
    assert "0x00000042" in d["regs"][1]
