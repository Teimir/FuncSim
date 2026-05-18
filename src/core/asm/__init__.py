"""E32C assembler package."""

from core.asm.driver import (
    AsmResult,
    assemble_file,
    assemble_text,
    assemble_text_with_listing,
)
from core.asm.encode import assemble_line
from core.asm.errors import AssembleError
from core.asm.link import LinkSpec, link_programs
from core.asm.listing import format_listing

__all__ = [
    "AssembleError",
    "AsmResult",
    "LinkSpec",
    "assemble_file",
    "assemble_line",
    "assemble_text",
    "assemble_text_with_listing",
    "format_listing",
    "link_programs",
]
