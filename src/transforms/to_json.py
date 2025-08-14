import json
from pathlib import Path
from typing import Any, Dict

def dump_json(obj: Dict[str, Any], out_path: str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2))# Placeholder - will add content later
