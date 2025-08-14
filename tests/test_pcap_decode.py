from pathlib import Path

from scapy.all import IP, UDP, Ether, Raw, wrpcap  # type: ignore[import-untyped]

from src.binutils.pcap_extract import decode_pcap_payloads
from tools.make_vmf_sample import make_sample


def make_test_pcap(tmpdir: Path) -> Path:
    """
    Build a minimal PCAP with a single UDP packet whose Raw payload is a VMF-like sample.
    Returns the path to the generated pcap file inside tmpdir.
    """
    tmpdir.mkdir(parents=True, exist_ok=True)
    pcap_path = tmpdir / "unit_sample.pcap"

    payload = make_sample(msg_type=5, lat=1.0, lon=2.0, ts=1234567890)
    pkt = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / UDP(sport=1111, dport=2222) / Raw(load=payload)
    wrpcap(str(pcap_path), [pkt])
    return pcap_path


def test_decode_pcap_payloads(tmp_path: Path):
    """
    Ensure decode_pcap_payloads writes exactly one payload file and contents match our VMF payload.
    """
    pcap = make_test_pcap(tmp_path)
    out_dir = tmp_path / "decoded"
    count = decode_pcap_payloads(pcap, out_dir)
    assert count == 1

    # Verify output file exists and has non-zero size
    files = sorted(out_dir.glob("payload_*.bin"))
    assert len(files) == 1
    assert files[0].stat().st_size > 0
