from lxml import etree
from typing import Dict, Any

def parse_cot_xml(data: bytes) -> Dict[str, Any]:
    """
    Minimal CoT parser: extracts key attributes from <event> and nested <point>.
    Returns a simple dict the normalizer can consume.
    """
    root = etree.fromstring(data)

    if root.tag != "event":
        raise ValueError("Expected CoT <event> as root element")

    event = {
        "type": root.get("type"),
        "uid": root.get("uid"),
        "how": root.get("how"),
        "time": root.get("time"),
        "start": root.get("start"),
        "stale": root.get("stale"),
        "detail": {},
        "point": {},
    }

    # <point lat="" lon="" hae="" ce="" le="" />
    point = root.find("point")
    if point is not None:
        event["point"] = {
            "lat": safe_float(point.get("lat")),
            "lon": safe_float(point.get("lon")),
            "hae": safe_float(point.get("hae")),
            "ce": safe_float(point.get("ce")),
            "le": safe_float(point.get("le")),
        }

    # <detail>…</detail> (we just capture attributes of the first level)
    detail = root.find("detail")
    if detail is not None:
        event["detail"] = {k: v for k, v in detail.attrib.items()}

    return {"format": "cot", "raw": event}

def safe_float(x):
    try:
        return float(x) if x is not None else None
    except Exception:
        return None# Placeholder - will add content later
