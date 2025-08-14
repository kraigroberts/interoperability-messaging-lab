#!/usr/bin/env python3
"""
Generate a minimal VMF-like binary sample that matches src/parsers/vmf_parser.py.

Binary layout (little-endian):
- magic     : 4s  -> b"VMF1"
- msg_type  : H   -> uint16
- latitude  : d   -> float64
- longitude : d   -> float64
- timestamp : Q   -> uint64 (epoch seconds)

Total bytes: 30
"""

import struct
import time
from pathlib import Path

_HEADER_FMT = "<4sHddQ"

def make_sample(
    msg_type: int = 42,
    lat: float = 38.7000,
    lon: float = -77.2000,
    ts: int | None = None,
) -> bytes:
    if ts is None:
        ts = int(time.time())
    return struct.pack(_HEADER_FMT, b"VMF1", msg_type, float(lat), float(lon), int(ts))

def write_sample(out_path: str) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(make_sample())
    return p

if __name__ == "__main__":
    # Default location: data/samples/sample_vmf.bin
    out = write_sample("data/samples/sample_vmf.bin")
    print(f"Wrote VMF sample to {out.resolve()}")
