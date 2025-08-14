import struct
from typing import Any, Dict

"""
Minimal VMF-like binary parser for demonstration and testing.

Binary framing (little-endian):
- magic      : 4s     -> must be b"VMF1"
- msg_type   : H      -> uint16
- latitude   : d      -> float64
- longitude  : d      -> float64
- timestamp  : Q      -> uint64 (epoch seconds)

Total bytes: 4 + 2 + 8 + 8 + 8 = 30 bytes

This is NOT an official VMF spec. It's a safe stand-in to demonstrate
binary parsing, field extraction, and normalization without sharing
controlled formats. Replace with a real parser later if needed.
"""

_HEADER_FMT = "<4sHddQ"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)

def parse_vmf_binary(data: bytes) -> Dict[str, Any]:
    if len(data) < _HEADER_SIZE:
        raise ValueError(f"VMF sample too short: {len(data)} bytes (need {_HEADER_SIZE})")

    magic, msg_type, lat, lon, ts = struct.unpack_from(_HEADER_FMT, data, 0)
    if magic != b"VMF1":
        raise ValueError(f"Bad magic header: {magic!r} (expected b'VMF1')")

    return {
        "format": "vmf",
        "raw": {
            "msg_type": int(msg_type),
            "lat": float(lat),
            "lon": float(lon),
            "timestamp": int(ts),
        },
    }
