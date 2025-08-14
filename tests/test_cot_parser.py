from src.parsers.cot_parser import parse_cot_xml
from src.transforms.normalize_schema import normalize_message


def test_cot_parse_and_normalize():
    sample = b"""
    <event version="2.0" uid="T-123" type="a-f-A" how="m-g"
           time="2025-08-14T12:00:00Z" start="2025-08-14T12:00:00Z" stale="2025-08-14T13:00:00Z">
      <point lat="38.7" lon="-77.2" hae="100.0" ce="30.0" le="10.0"/>
      <detail callsign="VIKING11"/>
    </event>
    """
    parsed = parse_cot_xml(sample)
    norm = normalize_message(parsed)

    assert norm["source_format"] == "cot"
    assert norm["id"] == "T-123"
    assert norm["position"]["lat"] == 38.7
    assert norm["detail"]["callsign"] == "VIKING11"
