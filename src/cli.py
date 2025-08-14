#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from rich import print

from src.parsers.cot_parser import parse_cot_xml
from src.parsers.vmf_parser import parse_vmf_binary
from src.transforms.normalize_schema import normalize_message
from src.transforms.to_json import dump_json
from src.binutils.pcap_extract import decode_pcap_payloads


def cmd_parse(args: argparse.Namespace) -> None:
    in_path = Path(args.infile)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    data = in_path.read_bytes()

    if args.format == "cot":
        parsed = parse_cot_xml(data)
    elif args.format == "vmf":
        parsed = parse_vmf_binary(data)
    else:
        raise ValueError(f"Unsupported format: {args.format}")

    normalized = normalize_message(parsed)

    if args.out:
        dump_json(normalized, args.out)
        print(f"[green]Wrote[/green] {args.out}")
    else:
        print(json.dumps(normalized, indent=2))


def cmd_pcap_decode(args: argparse.Namespace) -> None:
    pcap_path = Path(args.pcap)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = decode_pcap_payloads(pcap_path, out_dir)
    print(f"[green]Decoded[/green] {count} payload(s) to {out_dir}")


def main():
    ap = argparse.ArgumentParser(
        prog="interop-cli",
        description="Interoperability Messaging Lab CLI"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    # parse subcommand
    ap_parse = sub.add_parser("parse", help="Parse a message file")
    ap_parse.add_argument("format", choices=["cot", "vmf"], help="message format")
    ap_parse.add_argument("--in", dest="infile", required=True, help="input file path")
    ap_parse.add_argument("--out", dest="out", help="output JSON path (optional)")
    ap_parse.set_defaults(func=cmd_parse)

    # pcap subcommand
    ap_pcap = sub.add_parser("pcap", help="PCAP utilities")
    pcap_sub = ap_pcap.add_subparsers(dest="pcmd", required=True)

    ap_pcap_decode = pcap_sub.add_parser("decode", help="Decode Raw TCP/UDP payloads from a PCAP")
    ap_pcap_decode.add_argument("--pcap", required=True, help="pcap file path")
    ap_pcap_decode.add_argument("--out", required=True, help="output directory")
    ap_pcap_decode.set_defaults(func=cmd_pcap_decode)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
