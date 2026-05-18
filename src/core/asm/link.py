"""Link multiple object files into one image."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.asm.driver import assemble_file
from core.asm.errors import AssembleError


@dataclass
class LinkSpec:
    path: Path | str
    origin: int = 0
    name: str | None = None

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.name is None:
            self.name = self.path.name


def link_programs(
    specs: list[LinkSpec],
    *,
    image_size: int | None = None,
    fill: int = 0,
) -> list[int]:
    """Link segments; image_size is minimum word count (padding with fill)."""
    if not specs:
        return []
    image: dict[int, int] = {}
    min_origin = min(spec.origin for spec in specs)
    for spec in specs:
        words = assemble_file(spec.path, origin=spec.origin)
        for i, w in enumerate(words):
            addr = spec.origin + i * 4
            if addr in image and image[addr] != w:
                raise AssembleError(
                    f"segment overlap at 0x{addr:x}: {spec.name!r} conflicts with prior segment"
                )
            image[addr] = w
    if not image:
        return []
    max_addr = max(image.keys())
    end = max_addr + 4
    words = [image.get(min_origin + off, fill) for off in range(0, end - min_origin, 4)]
    if image_size is not None and len(words) < image_size:
        words.extend([fill] * (image_size - len(words)))
    return words
