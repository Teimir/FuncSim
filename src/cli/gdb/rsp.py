"""GDB Remote Serial Protocol framing (checksum, escape)."""

from __future__ import annotations

RSP_ACK = b"+"
RSP_NACK = b"-"


def checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def escape_payload(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b in (ord(b"$"), ord(b"#"), ord(b"}"), ord(b"*")):
            out.append(ord(b"}"))
            out.append(b ^ 0x20)
        else:
            out.append(b)
    return bytes(out)


def encode_packet(payload: str) -> bytes:
    body = payload.encode("ascii")
    esc = escape_payload(body)
    cs = checksum(esc)
    return b"$" + esc + f"#{cs:02x}".encode("ascii")


def read_packet_from_stream(read_byte) -> str | None:
    """Read one RSP packet; read_byte() -> one byte or b'' on EOF. Returns payload or None."""
    while True:
        b = read_byte()
        if not b:
            return None
        if b == b"$":
            break
    payload = bytearray()
    while True:
        b = read_byte()
        if not b:
            return None
        if b == b"#":
            break
        if b == b"}":
            n = read_byte()
            if not n:
                return None
            payload.append(n[0] ^ 0x20)
        else:
            payload.append(b[0])
    hi = read_byte()
    lo = read_byte()
    if not hi or not lo:
        return None
    try:
        got = int(hi + lo, 16)
    except ValueError:
        return None
    if checksum(payload) != got:
        return None
    return payload.decode("ascii", errors="replace")
