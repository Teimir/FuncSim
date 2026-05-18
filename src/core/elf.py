"""Minimal ELF32 little-endian support for E32C (EM_E32C = 0xE32C)."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

# Machine type: matches CORE_INFO magic in docs/isa/cores.yaml
EM_E32C = 0xE32C

ELFMAG = b"\x7fELF"
ELFCLASS32 = 1
ELFDATA2LSB = 1
EV_CURRENT = 1
ET_EXEC = 2
PT_LOAD = 1
PF_R = 4
PF_W = 2
PF_X = 1

EI_NIDENT = 16
Ehdr = struct.Struct("<16sHHIIIIIHHHHHH")
Phdr = struct.Struct("<IIIIIIII")
Shdr = struct.Struct("<IIIIIIIIII")


@dataclass
class ElfSegment:
    vaddr: int
    data: bytes
    paddr: int | None = None
    flags: int = PF_R | PF_X

    def __post_init__(self) -> None:
        self.vaddr &= 0xFFFFFFFF
        if self.paddr is None:
            self.paddr = self.vaddr
        else:
            self.paddr &= 0xFFFFFFFF


@dataclass
class ElfSymbol:
    name: str
    value: int
    size: int = 0
    bind: int = 1  # STB_GLOBAL
    type: int = 2  # STT_FUNC


@dataclass
class ElfImage:
    entry: int
    segments: list[ElfSegment] = field(default_factory=list)
    symbols: list[ElfSymbol] = field(default_factory=list)

    def loadable_blob(self) -> tuple[int, bytes]:
        """Return (base_vaddr, contiguous PT_LOAD bytes) for a single RAM image."""
        if not self.segments:
            return 0, b""
        segs = sorted(self.segments, key=lambda s: s.vaddr)
        base = segs[0].vaddr
        end = base
        for s in segs:
            end = max(end, s.vaddr + len(s.data))
        blob = bytearray(end - base)
        for s in segs:
            off = s.vaddr - base
            blob[off : off + len(s.data)] = s.data
        return base, bytes(blob)

    def words_at(self, base: int | None = None) -> tuple[int, list[int]]:
        """Decode loadable image as 32-bit little-endian words."""
        img_base, blob = self.loadable_blob()
        load_base = img_base if base is None else base
        words = [struct.unpack_from("<I", blob, i)[0] & 0xFFFFFFFF for i in range(0, len(blob), 4)]
        return load_base, words


class ElfError(ValueError):
    """Invalid or unsupported ELF for E32C."""


def _align4(n: int) -> int:
    return (n + 3) & ~3


def parse_elf32(path: Path | str) -> ElfImage:
    data = Path(path).read_bytes()
    if len(data) < Ehdr.size:
        raise ElfError("file too small for ELF header")
    ident, etype, machine, _ver, entry, phoff, shoff, flags, ehsize, phentsize, phnum, shentsize, shnum, shstrndx = (
        Ehdr.unpack_from(data, 0)
    )
    if ident[:4] != ELFMAG:
        raise ElfError("not an ELF file")
    if ident[4] != ELFCLASS32 or ident[5] != ELFDATA2LSB:
        raise ElfError("expected ELF32 little-endian")
    if machine != EM_E32C:
        raise ElfError(f"e_machine 0x{machine:x}, expected EM_E32C (0x{EM_E32C:x})")
    if etype not in (ET_EXEC, 1):  # ET_REL=1 tolerated for linked objects
        raise ElfError(f"unsupported e_type {etype}")

    segments: list[ElfSegment] = []
    for i in range(phnum):
        off = phoff + i * phentsize
        if off + Phdr.size > len(data):
            raise ElfError("truncated program header table")
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, _align = Phdr.unpack_from(data, off)
        if p_type != PT_LOAD or p_filesz == 0:
            continue
        if p_offset + p_filesz > len(data):
            raise ElfError("segment extends past end of file")
        seg_data = data[p_offset : p_offset + p_filesz]
        if p_memsz > p_filesz:
            seg_data = seg_data + bytes(p_memsz - p_filesz)
        segments.append(ElfSegment(vaddr=p_vaddr, paddr=p_paddr, data=seg_data, flags=p_flags))

    symbols: list[ElfSymbol] = []
    if shoff and shnum and shentsize == Shdr.size:
        sections = []
        for i in range(shnum):
            soff = shoff + i * shentsize
            sections.append(Shdr.unpack_from(data, soff))
        strtab: bytes = b""
        symtab_off = 0
        symtab_size = 0
        symtab_link = 0
        for sh_name, sh_type, _sh_flags, _sh_addr, sh_offset, sh_size, sh_link, _sh_info, _sh_addralign, _sh_entsize in sections:
            if sh_type == 3 and sh_link < shnum:  # SHT_STRTAB
                _, _, _, _, st_off, st_size, _, _, _, _ = sections[sh_link]
                strtab = data[st_off : st_off + st_size]
            if sh_type == 2:  # SHT_SYMTAB
                symtab_off = sh_offset
                symtab_size = sh_size
                symtab_link = sh_link
        if symtab_off and symtab_size >= 16:
            st_off = sections[symtab_link][4] if symtab_link < len(sections) else 0
            st_data = data[st_off : st_off + sections[symtab_link][5]] if symtab_link < len(sections) else strtab
            nsym = symtab_size // 16
            for si in range(1, nsym):
                sym_off = symtab_off + si * 16
                name_idx, value, size, info, _other, shndx = struct.unpack_from("<IIIBBH", data, sym_off)
                if shndx == 0:
                    continue
                name = _strtab_name(st_data, name_idx)
                if name:
                    symbols.append(
                        ElfSymbol(
                            name=name,
                            value=value & 0xFFFFFFFF,
                            size=size,
                            bind=(info >> 4) & 0xF,
                            type=info & 0xF,
                        )
                    )

    return ElfImage(entry=entry & 0xFFFFFFFF, segments=segments, symbols=symbols)


def _strtab_name(strtab: bytes, index: int) -> str:
    if index >= len(strtab):
        return ""
    end = strtab.find(b"\x00", index)
    if end < 0:
        end = len(strtab)
    return strtab[index:end].decode("utf-8", errors="replace")


def write_elf32_exec(
    path: Path | str,
    segments: list[ElfSegment],
    *,
    entry: int = 0,
    symbols: list[ElfSymbol] | None = None,
) -> None:
    """Write a static ET_EXEC ELF32 with PT_LOAD segments and optional symbol table."""
    path = Path(path)
    if not segments:
        raise ElfError("no segments to write")

    segs = sorted(segments, key=lambda s: s.vaddr)
    # Lay out PT_LOAD payloads back-to-back in the file
    file_off = Ehdr.size + len(segs) * Phdr.size
    phdrs: list[tuple[int, int, int, int, int, int, int, int]] = []
    payload = bytearray()
    for s in segs:
        aligned = _align4(len(s.data))
        chunk = s.data + bytes(aligned - len(s.data))
        p_offset = file_off + len(payload)
        payload.extend(chunk)
        memsz = len(s.data)
        phdrs.append(
            (
                PT_LOAD,
                p_offset,
                s.vaddr & 0xFFFFFFFF,
                (s.paddr if s.paddr is not None else s.vaddr) & 0xFFFFFFFF,
                len(s.data),
                memsz,
                s.flags,
                4,
            )
        )

    sym_section = b""
    str_section = b"\x00"
    shdrs_extra: list[bytes] = []
    sh_link_str = 0
    if symbols:
        str_offs = {0: 0}
        str_blob = bytearray(b"\x00")
        for sym in symbols:
            if sym.name not in str_offs:
                str_offs[sym.name] = len(str_blob)
                str_blob.extend(sym.name.encode("utf-8"))
                str_blob.append(0)
        str_section = bytes(str_blob)
        sym_entries = bytearray(16)  # null symbol
        for sym in symbols:
            name_idx = str_offs.get(sym.name, 0)
            info = ((sym.bind & 0xF) << 4) | (sym.type & 0xF)
            sym_entries.extend(struct.pack("<IIIBBH", name_idx, sym.value & 0xFFFFFFFF, sym.size, info, 0, 1))
        sym_section = bytes(sym_entries)

    # Section headers after file payload
    sh_base = file_off + len(payload)
    n_sh = 1 + (2 if symbols else 0) + (1 if symbols else 0)  # NULL + symtab + strtab
    e_shoff = sh_base
    e_shnum = n_sh
    e_shstrndx = n_sh - 1 if symbols else 0

    out = bytearray()
    ehdr = Ehdr.pack(
        ELFMAG + bytes([ELFCLASS32, ELFDATA2LSB, EV_CURRENT, 0]) + bytes(8),
        ET_EXEC,
        EM_E32C,
        1,
        entry & 0xFFFFFFFF,
        Ehdr.size,
        e_shoff if symbols else 0,
        0,
        Ehdr.size,
        Phdr.size,
        len(phdrs),
        Shdr.size if symbols else 0,
        e_shnum if symbols else 0,
        e_shstrndx if symbols else 0,
    )
    out.extend(ehdr)
    for ph in phdrs:
        out.extend(Phdr.pack(*ph))
    out.extend(payload)

    if symbols:
        # .shstrtab names
        shstr = b"\x00.symtab\0.strtab\0.shstrtab\0"
        sym_off = len(out)
        out.extend(sym_section)
        str_off = len(out)
        out.extend(str_section)
        shstr_off = len(out)
        out.extend(shstr)

        def _shdr(name_off: int, sh_type: int, offset: int, size: int, link: int = 0) -> bytes:
            return Shdr.pack(name_off, sh_type, 0, 0, offset, size, link, 0, 4, 16 if sh_type == 2 else 0)

        shdrs_extra = [
            _shdr(0, 0, 0, 0),  # SHT_NULL
            _shdr(shstr.find(b".symtab"), 2, sym_off, len(sym_section), sh_link_str + 1),
            _shdr(shstr.find(b".strtab"), 3, str_off, len(str_section)),
            _shdr(shstr.find(b".shstrtab"), 3, shstr_off, len(shstr)),
        ]
        out.extend(b"".join(shdrs_extra))

    path.write_bytes(bytes(out))


def words_to_segment(words: list[int], *, vaddr: int = 0, fill: int = 0) -> ElfSegment:
    blob = b"".join(struct.pack("<I", w & 0xFFFFFFFF) for w in words)
    if fill and len(blob) % 4:
        blob += bytes(4 - len(blob) % 4)
    return ElfSegment(vaddr=vaddr, data=blob, flags=PF_R | PF_W | PF_X)
