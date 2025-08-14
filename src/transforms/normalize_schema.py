from typing import Dict, Any

def normalize_message(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert parsed messages into a normalized schema we can reuse across formats.
    Supports:
      - CoT (XML) via parse_cot_xml(...)
      - VMF (binary demo format) via parse_vmf_binary(...)
    """
    fmt = parsed.get("format")

    if fmt == "cot":
        ev = parsed["raw"]
        return {
            "schema_version": "1.0",
            "source_format": "cot",
            "id": ev.get("uid"),
            "type": ev.get("type"),
            "how": ev.get("how"),
            "time": {
                "reported": ev.get("time"),
                "start": ev.get("start"),
                "stale": ev.get("stale"),
            },
            "position": {
                "lat": ev.get("point", {}).get("lat"),
                "lon": ev.get("point", {}).get("lon"),
                "hae": ev.get("point", {}).get("hae"),
                "ce": ev.get("point", {}).get("ce"),
                "le": ev.get("point", {}).get("le"),
            },
            "detail": ev.get("detail", {}),
        }

    if fmt == "vmf":
        rv = parsed["raw"]
        return {
            "schema_version": "1.0",
            "source_format": "vmf",
            "id": None,
            "type": f"vmf:{rv.get('msg_type')}",
            "how": None,
            "time": {
                "reported": rv.get("timestamp"),
                "start": rv.get("timestamp"),
                "stale": None,
            },
            "position": {
                "lat": rv.get("lat"),
                "lon": rv.get("lon"),
                "hae": None,
                "ce": None,
                "le": None,
            },
            "detail": {},
        }

    raise ValueError(f"Unsupported parsed format: {fmt!r}")
