#!/usr/bin/env python3
"""
Generate a minimal PCAP that contains one UDP packet whose payload is the
VMF-like binary produced by tools/make_vmf_sample.py. The PCAP is written to:
  data/pcaps/example_capture.pcap

This lets you demo:
  python src/cli.py pcap decode --pcap data/pcaps/example_capture.pcap --out out/
"""

from pathlib import Path
from scapy.all import Ether, IP, UDP, Raw, wrpcap  # type: ignore[import-untyped]
from tools.make_vmf_sample import make_sample


def build_packet() -> Ether:
    vmf_payload = make_sample(msg_type=99, lat=38.7000, lon=-77.2000, ts=1_725_000_000)
    # Simple L2/L3/L4 stack with arbitrary addresses/ports
    pkt = (
        Ether(src="02:42:ac:11:00:02", dst="02:42:ac:11:00:03")
        / IP(src="192.168.1.10", dst="192.168.1.20")
        / UDP(sport=40000, dport=40001)
        / Raw(load=vmf_payload)
    )
    return pkt


def write_pcap(out_path: str = "data/pcaps/example_capture.pcap") -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    pkt = build_packet()
    wrpcap(str(p), [pkt])
    return p


if __name__ == "__main__":
    out = write_pcap()
    print(f"Wrote PCAP sample to {out.resolve()}")
