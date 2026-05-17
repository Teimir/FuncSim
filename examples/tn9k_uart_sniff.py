#!/usr/bin/env python3
"""Read Tang Nano 9K UART on all serial COM ports (find the USB-UART, not JTAG)."""

from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Install pyserial: pip install pyserial", file=sys.stderr)
    raise SystemExit(1)


def sniff(port: str, baud: int, seconds: float) -> bytes:
    with serial.Serial(port, baud, timeout=0.05) as ser:
        time.sleep(0.05)
        ser.reset_input_buffer()
        end = time.monotonic() + seconds
        buf = bytearray()
        while time.monotonic() < end:
            chunk = ser.read(4096)
            if chunk:
                buf.extend(chunk)
        return bytes(buf)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seconds", type=float, default=2.0, help="listen time per port/baud")
    p.add_argument("--bauds", type=int, nargs="+", default=[115200, 9600])
    args = p.parse_args()

    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found. Is the board plugged in?")
        return 1

    print("Serial ports on this PC:")
    for info in ports:
        print(f"  {info.device}: {info.description!r} hwid={info.hwid!r}")

    print("\nListening (FPGA bring-up should send 0x55 or 'H', NOT only 0x0A):\n")
    for info in ports:
        for baud in args.bauds:
            try:
                data = sniff(info.device, baud, args.seconds)
            except serial.SerialException as exc:
                print(f"{info.device} @ {baud}: OPEN FAILED — {exc}")
                continue
            if not data:
                print(f"{info.device} @ {baud}: (no data)")
                continue
            uniq = sorted(set(data))
            preview = data[:64]
            print(
                f"{info.device} @ {baud}: {len(data)} bytes, "
                f"unique={''.join(f'{b:02x}' for b in uniq)}, "
                f"preview={preview!r}"
            )
            if data == bytes([0x0A]) * len(data):
                print("  ^ only 0x0A — likely wrong port, wrong baud, or terminal echo")

    print(
        "\nTip: TN9K exposes two USB serial devices. Use the one that shows "
        "CH340/CDC UART (not only JTAG). Try both COM ports at 115200."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
