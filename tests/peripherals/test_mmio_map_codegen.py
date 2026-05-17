from pathlib import Path

import yaml

from core.mmio_constants import GPIO_OFFSET, MMIO_BASE_DEFAULT, UART_OFFSET
from scripts.gen_mmio import main as gen_main


def test_mmio_offsets_match_yaml() -> None:
    root = Path(__file__).resolve().parents[2]
    doc = yaml.safe_load((root / "docs" / "isa" / "mmio_map.yaml").read_text(encoding="utf-8"))
    dev = doc["devices"]
    def _off(key: str) -> int:
        v = dev[key]["offset"]
        if isinstance(v, int):
            return v
        return int(str(v), 0)

    assert GPIO_OFFSET == _off("gpio")
    assert UART_OFFSET == _off("uart")
    base = doc["mmio_base"]
    assert MMIO_BASE_DEFAULT == (int(base, 0) if isinstance(base, str) else int(base))


def test_gen_mmio_idempotent() -> None:
    gen_main()
    gen_main()
