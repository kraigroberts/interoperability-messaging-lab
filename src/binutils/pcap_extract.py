from pathlib import Path
from typing import Union

from scapy.all import rdpcap, Raw, TCP, UDP  # type: ignore[import-untyped]


def decode_pcap_payloads(pcap_path: Union[str, Path], out_dir: Union[str, Path]) -> int:
    """
    Reads a PCAP file and writes application-layer payloads (TCP/UDP Raw)
    to individual files in `out_dir` as payload_0001.bin, payload_0002.bin, ...

    Returns:
        int: number of payload files written.
    """
    pcap_path = Path(pcap_path)
    out_dir = Path(out_dir)
    if not pcap_path.exists():
        raise FileNotFoundError(f"PCAP not found: {pcap_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    packets = rdpcap(str(pcap_path))

    count = 0
    for pkt in packets:
        # Only capture payloads from TCP/UDP that actually have Raw data
        if (TCP in pkt or UDP in pkt) and Raw in pkt:
            count += 1
            payload = bytes(pkt[Raw].load)
            fname = out_dir / f"payload_{count:04d}.bin"
            fname.write_bytes(payload)

    return count
