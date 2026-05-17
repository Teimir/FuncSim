"""TCP GDB Remote Serial Protocol server for the E32C functional simulator."""

from __future__ import annotations

import argparse
import socket
import sys

from cli.debug_common import (
    add_sim_session_arguments,
    create_debug_controller,
    load_initial_image,
)
from cli.gdb.stub import GdbStub
from core.memory import Memory


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="E32C GDB remote stub (RSP over TCP)")
    add_sim_session_arguments(p)
    p.add_argument("--port", type=int, default=3333, help="TCP port (default 3333)")
    p.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1)")
    args = p.parse_args(argv)

    if not args.hex and not args.bin:
        print("gdb_server: provide --hex or --bin", file=sys.stderr)
        return 2

    ram = Memory()
    ctrl = create_debug_controller(ram, args)
    load_initial_image(ctrl, args)

    stub = GdbStub(ctrl)
    host, port = args.host, args.port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(1)
        print(f"E32C GDB server listening on {host}:{port}", flush=True)
        conn, addr = srv.accept()
        print(f"GDB connected from {addr[0]}:{addr[1]}", flush=True)
        with conn:
            conn_file = conn.makefile("rwb", buffering=0)
            try:
                stub.serve(conn_file)
            finally:
                conn_file.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
