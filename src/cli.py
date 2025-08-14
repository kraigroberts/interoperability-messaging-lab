#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from rich import print

from src.parsers.cot_parser import parse_cot_xml
from src.transforms.normalize_schema import normalize_message
from src.transforms.to_json import dump_json

def cmd_parse(args: argparse.Namespace) -> None:
    in_path = Path(args.infile)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    if args.format != "cot":
        raise ValueError("This starter supports only 'cot' for now. (VMF/STANAG coming next.)")

    data = in_path.read_bytes()
    parsed = parse_cot_xml(data)
    normalized = normalize_message(parsed)

    if args.out:
        dump_json(normalized, args.out)
        print(f"[green]Wrote[/green] {args.out}")
    else:
        print(json.dumps(normalized, indent=2))

def main():
    ap = argparse.ArgumentParser(prog="interop-cli", description="Interoperability Messaging Lab CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_parse = sub.add_parser("parse", help="Parse a message file")
    ap_parse.add_argument("format", choices=["cot"], help="message format (cot only in starter)")
    ap_parse.add_argument("--in", dest="infile", required=True, help="input file path")
    ap_parse.add_argument("--out", dest="out", help="output JSON path (optional)")
    ap_parse.set_defaults(func=cmd_parse)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
