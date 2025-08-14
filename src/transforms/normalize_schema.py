from typing import Dict, Any

def normalize_message(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert parsed CoT into a normalized schema we can reuse across formats.
    """
    if parsed.get("format") != "cot":
        raise ValueError("Normalizer expected format='cot'")

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
    }# Placeholder - will add content later
