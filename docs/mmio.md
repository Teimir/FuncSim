# MMIO map (E32C functional simulator)

Default base: `0xFFFF_0000` (`MMIO_BASE_DEFAULT`). All accesses are **32-bit word aligned** (see `SystemBus.read_word` / `write_word`).

Window size: **`0x4000`** bytes from `mmio_base` (devices must live in `[mmio_base, mmio_base + 0x4000)`).

## Layout (offset from `mmio_base`)

| Offset (hex) | Device | Size (hex) | Notes |
|-------------|--------|------------|--------|
| `0x0000` | GPIO | `0x4` | Single word: output latch read/write |
| `0x1000` | UART | `0x10` | See UART registers below |
| `0x2000` | Timer | `0x20` | Cycle compare + IRQ; see `CycleTimer` |
| `0x3000` | SD / block storage | `0x210` | Functional block device (not SPI protocol) |

Legacy programs using only GPIO/UART/Timer are unaffected: their offsets are unchanged.

## UART (`+0x1000`)

| Offset | Name | Access |
|--------|------|--------|
| `+0x0` | TX | Write: enqueue TX byte (low 8 bits) |
| `+0x4` | RX | Read: dequeue RX byte |
| `+0x8` | STATUS | Read: `RX_READY`, `TX_IDLE` flags |

## Timer (`+0x2000`)

See [`src/core/peripherals/timer.py`](../src/core/peripherals/timer.py): cycle counter low/high, compare low/high, control (IRQ enable, pending, ACK W1C).

## SD / block storage (`+0x3000`)

512-byte sectors, LBA is a 32-bit sector index. Backed by a **host file** (binary image) when mounted.

| Offset | Name | Access |
|--------|------|--------|
| `+0x00` | CTRL | Write: start command in **low byte** — `1` = read sector into buffer, `2` = write buffer to sector, `3` = flush file. Read returns `0`. |
| `+0x04` | STATUS | Read only: `READY(1)`, `ERROR(4)`, `NO_MEDIUM(8)`; error code in bits `16–23` if `ERROR`. |
| `+0x08` | LBA | Read/write: sector index for next read/write command. |
| `+0x10` … `+0x20C` | DATA | 128 words (512 bytes) sector buffer; little-endian words. |

**Read flow:** set `LBA`, write `CTRL = 1`. When `STATUS` has `READY` and not `ERROR`, read DATA aperture.

**Write flow:** set `LBA`, fill DATA aperture, write `CTRL = 2`.

File length must be a multiple of 512 when mounting an existing image (otherwise mount fails / reports error).

## Python / CLI

- `SystemBus(..., sd_image=Path | None, sd_create_sectors=int | None)`
- Flags: `--sd-image`, `--sd-create-sectors` (where applicable) on `cli.sim`, `cli.debug`, `cli.debug_gui`.
