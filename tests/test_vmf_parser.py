from src.parsers.vmf_parser import parse_vmf_binary
from src.transforms.normalize_schema import normalize_message
from tools.make_vmf_sample import make_sample


def test_vmf_parse_and_normalize():
    # Build a valid VMF-like binary matching our parser's format
    sample = make_sample(msg_type=7, lat=38.7, lon=-77.2, ts=1_725_000_000)

    parsed = parse_vmf_binary(sample)
    norm = normalize_message(parsed)

    assert norm["source_format"] == "vmf"
    assert norm["type"] == "vmf:7"
    assert norm["position"]["lat"] == 38.7
    assert norm["position"]["lon"] == -77.2
    assert norm["time"]["reported"] == 1_725_000_000
