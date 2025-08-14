#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

from rich import print

try:
    from .binutils.pcap_extract import decode_pcap_payloads
    from .parsers.cot_parser import parse_cot_xml
    from .parsers.vmf_parser import parse_vmf_binary
    from .stream.pub import create_publisher
    from .stream.sub import create_subscriber
    from .transforms.exporters import export_messages
    from .transforms.normalize_schema import normalize_message
except ImportError:
    # Fallback for when running as script
    from binutils.pcap_extract import decode_pcap_payloads
    from parsers.cot_parser import parse_cot_xml
    from parsers.vmf_parser import parse_vmf_binary
    from stream.pub import create_publisher
    from stream.sub import create_subscriber
    from transforms.exporters import export_messages
    from transforms.normalize_schema import normalize_message


def cmd_parse(args: argparse.Namespace) -> None:
    """Parse and normalize tactical message files."""
    print(f"[blue]Parsing[/blue] {args.format.upper()} message from {args.infile}")
    
    in_path = Path(args.infile)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    # Read and parse file
    data = in_path.read_bytes()
    print(f"[blue]Read[/blue] {len(data)} bytes")

    if args.format == "cot":
        print("[blue]Parsing[/blue] CoT XML format...")
        parsed = parse_cot_xml(data)
    elif args.format == "vmf":
        print("[blue]Parsing[/blue] VMF binary format...")
        parsed = parse_vmf_binary(data)
    else:
        raise ValueError(f"Unsupported format: {args.format}")

    print("[blue]Normalizing[/blue] message to standard schema...")
    normalized = normalize_message(parsed)

    if args.out:
        # Use specified output format or default to JSON
        output_format = getattr(args, 'out_format', 'json')
        print(f"[blue]Exporting[/blue] to {output_format.upper()} format...")
        count = export_messages([normalized], args.out, output_format)
        print(f"[green]✅ Successfully wrote[/green] {args.out}")
        print(f"[green]   →[/green] {count} message exported in {output_format.upper()} format")
        print(f"[green]   →[/green] File size: {Path(args.out).stat().st_size} bytes")
    else:
        print("[blue]Displaying[/blue] normalized message:")
        print(json.dumps(normalized, indent=2))


def cmd_pcap_decode(args: argparse.Namespace) -> None:
    """Decode PCAP file and extract message payloads."""
    print(f"[blue]Decoding[/blue] PCAP file: {args.pcap}")
    
    pcap_path = Path(args.pcap)
    if not pcap_path.exists():
        raise FileNotFoundError(f"PCAP file not found: {pcap_path}")
    
    out_dir = Path(args.out)
    print(f"[blue]Output[/blue] directory: {out_dir}")
    
    # Create output directory
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[blue]Created[/blue] output directory")
    
    # Decode PCAP
    print("[blue]Processing[/blue] PCAP file and extracting payloads...")
    count = decode_pcap_payloads(pcap_path, out_dir)
    
    if count > 0:
        print(f"[green]✅ Successfully decoded[/green] {count} payload(s)")
        print(f"[green]   →[/green] Output directory: {out_dir}")
        print(f"[green]   →[/green] Files created: {len(list(out_dir.glob('*')))}")
    else:
        print(f"[yellow]⚠️  No payloads found[/yellow] in PCAP file")
        print(f"[yellow]   →[/yellow] Output directory: {out_dir}")


def cmd_stream_pub(args: argparse.Namespace) -> None:
    """Publish messages to ZeroMQ PUB socket."""
    print(f"[blue]Starting[/blue] ZeroMQ publisher on {args.bind}")
    print(f"[blue]Format[/blue]: {args.format.upper()}")
    print(f"[blue]Files[/blue]: {len(args.files)} file(s) specified")
    
    try:
        publisher = create_publisher(args.bind)
        print(f"[green]✅ Publisher[/green] initialized successfully")

        if args.stream:
            # Start continuous streaming
            print("[blue]Starting[/blue] continuous streaming mode...")
            file_paths = [Path(f) for f in args.files]
            publisher.start_streaming(file_paths, args.format, args.delay)

            try:
                print(f"[green]🔄 Streaming[/green] messages with {args.delay}s delay...")
                print("[yellow]Press Ctrl+C to stop streaming[/yellow]")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[yellow]Stopping[/yellow] stream...")
                publisher.stop_streaming()
                print("[green]✅ Stream stopped[/green]")
        else:
            # Publish once
            print("[blue]Publishing[/blue] messages once...")
            file_paths = [Path(f) for f in args.files]
            count = publisher.publish_from_files(file_paths, args.format, args.delay)
            print(f"[green]✅ Published[/green] {count} message(s)")

        publisher.close()
        print("[green]✅ Publisher[/green] closed")

    except Exception as e:
        print(f"[red]❌ Error[/red]: {e}")
        print(f"[red]   →[/red] Check file paths and network configuration")


def cmd_stream_sub(args: argparse.Namespace) -> None:
    """Subscribe to ZeroMQ PUB socket."""
    print(f"[blue]Starting[/blue] ZeroMQ subscriber")
    print(f"[blue]Connect[/blue]: {args.connect}")
    print(f"[blue]Topics[/blue]: {', '.join(args.topics)}")
    
    try:
        subscriber = create_subscriber(args.connect, args.topics)
        print(f"[green]✅ Subscriber[/green] initialized successfully")

        if args.timeout:
            print(f"[blue]Receiving[/blue] messages with {args.timeout}s timeout...")
            subscriber.start_receiving(args.timeout)
            print(f"[green]✅ Reception[/green] completed (timeout reached)")
        else:
            print("[blue]Receiving[/blue] messages indefinitely...")
            print("[yellow]Press Ctrl+C to stop receiving[/yellow]")
            subscriber.start_receiving()

    except Exception as e:
        print(f"[red]❌ Error[/red]: {e}")
        print(f"[red]   →[/red] Check network connection and publisher status")
        subscriber.close()
        print("[red]❌ Subscriber[/red] closed due to error")


def cmd_api(args: argparse.Namespace) -> None:
    """Start REST API server."""
    print(f"[blue]Starting[/blue] REST API server on {args.host}:{args.port}")
    
    try:
        import uvicorn
        from src.api.app import app
        
        print(f"[green]✅ API[/green] server initialized successfully")
        print(f"[blue]Documentation[/blue]: http://{args.host}:{args.port}/docs")
        print(f"[blue]Health Check[/blue]: http://{args.host}:{args.port}/health")
        print(f"[yellow]Press Ctrl+C to stop the server[/yellow]")
        
        # Start server
        uvicorn.run(
            "src.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"[red]❌ Error[/red]: Missing dependency - {e}")
        print(f"[red]   →[/red] Install with: pip install fastapi uvicorn[standard]")
    except Exception as e:
        print(f"[red]❌ Error[/red]: {e}")


def cmd_status(args: argparse.Namespace) -> None:
    """Show system status and configuration."""
    print("[blue]Interoperability Messaging Lab - System Status[/blue]")
    print("=" * 60)
    
    # Version info
    print(f"[green]Version[/green]: interop-cli 0.1.0")
    print(f"[green]Python[/green]: {sys.version.split()[0]}")
    
    # Check dependencies
    print("\n[blue]Dependencies[/blue]:")
    try:
        import lxml
        print(f"[green]✅ lxml[/green]: {lxml.__version__}")
    except ImportError:
        print("[red]❌ lxml[/red]: Not installed")
    
    try:
        import scapy
        print(f"[green]✅ scapy[/green]: {scapy.__version__}")
    except ImportError:
        print("[red]❌ scapy[/red]: Not installed")
    
    try:
        import zmq
        print(f"[green]✅ pyzmq[/green]: {zmq.__version__}")
    except ImportError:
        print("[red]❌ pyzmq[/red]: Not installed")
    
    try:
        import jsonschema
        print(f"[green]✅ jsonschema[/green]: {jsonschema.__version__}")
    except ImportError:
        print("[red]❌ jsonschema[/red]: Not installed")
    
    # Check sample data
    print("\n[blue]Sample Data[/blue]:")
    sample_dir = Path("data/samples")
    if sample_dir.exists():
        samples = list(sample_dir.glob("*"))
        print(f"[green]✅ Samples[/green]: {len(samples)} files found")
        for sample in samples:
            print(f"   → {sample.name}")
    else:
        print("[yellow]⚠️  Samples[/yellow]: No sample data directory found")
    
    # Check schema
    print("\n[blue]Schema[/blue]:")
    schema_file = Path("schema/normalized_message.schema.json")
    if schema_file.exists():
        print(f"[green]✅ Schema[/green]: {schema_file}")
        print(f"   → Size: {schema_file.stat().st_size} bytes")
    else:
        print("[red]❌ Schema[/red]: Schema file not found")
    
    print("\n[green]✅ Status check complete[/green]")


def cmd_interactive(args: argparse.Namespace) -> None:
    """Start interactive shell for exploration."""
    print("[blue]Interoperability Messaging Lab - Interactive Shell[/blue]")
    print("=" * 60)
    print("Type 'help' for available commands, 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            command = input("\n[blue]interop>[/blue] ").strip()
            
            if not command:
                continue
            elif command.lower() in ['quit', 'exit', 'q']:
                print("[green]Goodbye![/green]")
                break
            elif command.lower() == 'help':
                print_help()
            elif command.lower() == 'status':
                cmd_status(args)
            elif command.lower() == 'samples':
                show_samples()
            elif command.lower() == 'schema':
                show_schema()
            else:
                print(f"[yellow]Unknown command: {command}[/yellow]")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\n[green]Goodbye![/green]")
            break
        except EOFError:
            print("\n[green]Goodbye![/green]")
            break


def print_help():
    """Print interactive shell help."""
    print("\n[blue]Available Commands:[/blue]")
    print("  help     - Show this help message")
    print("  status   - Show system status")
    print("  samples  - List available sample files")
    print("  schema   - Show schema information")
    print("  quit     - Exit interactive shell")


def show_samples():
    """Show available sample files."""
    print("\n[blue]Sample Files:[/blue]")
    sample_dir = Path("data/samples")
    if sample_dir.exists():
        samples = list(sample_dir.glob("*"))
        for i, sample in enumerate(samples, 1):
            size = sample.stat().st_size
            print(f"  {i}. {sample.name} ({size} bytes)")
    else:
        print("[yellow]No sample directory found[/yellow]")


def show_schema():
    """Show schema information."""
    print("\n[blue]Schema Information:[/blue]")
    schema_file = Path("schema/normalized_message.schema.json")
    if schema_file.exists():
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        print(f"  Title: {schema.get('title', 'N/A')}")
        print(f"  Version: {schema.get('$schema', 'N/A')}")
        print(f"  Required fields: {', '.join(schema.get('required', []))}")
        print(f"  File size: {schema_file.stat().st_size} bytes")
    else:
        print("[red]Schema file not found[/red]")


def main():
    ap = argparse.ArgumentParser(
        prog="interop-cli",
        description="Interoperability Messaging Lab CLI - Tactical message parsing, validation, and streaming",
        epilog="""
Examples:
  # Parse a CoT XML message
  interop-cli parse cot --in data/samples/sample_cot.xml --out output.json

  # Export to different formats
  interop-cli parse cot --in file.xml --out output.csv --out-format csv

  # Stream messages via ZeroMQ
  interop-cli stream pub --in data/samples/*.xml --format cot --stream --delay 2.0

  # Subscribe to message stream
  interop-cli stream sub --connect tcp://localhost:5555

  # Decode PCAP and extract payloads
  interop-cli pcap decode --pcap capture.pcap --out output_dir

For more information, visit: https://github.com/kraigroberts/interoperability-messaging-lab
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # Add version and help options
    ap.add_argument("--version", action="version", version="interop-cli 0.1.0")
    
    sub = ap.add_subparsers(dest="cmd", required=True)

    # parse subcommand
    ap_parse = sub.add_parser("parse", help="Parse and normalize tactical message files")
    ap_parse.add_argument("format", choices=["cot", "vmf"], 
                         help="Message format: 'cot' for XML, 'vmf' for binary")
    ap_parse.add_argument("--in", dest="infile", required=True, 
                         help="Input file path (supports glob patterns)")
    ap_parse.add_argument("--out", dest="out", 
                         help="Output file path (if not specified, prints to stdout)")
    ap_parse.add_argument("--out-format", dest="out_format", 
                         choices=["json", "ndjson", "csv"],
                         default="json", 
                         help="Output format: json (default), ndjson, or csv")
    ap_parse.set_defaults(func=cmd_parse)

    # pcap subcommand
    ap_pcap = sub.add_parser("pcap", help="PCAP packet capture analysis and payload extraction")
    pcap_sub = ap_pcap.add_subparsers(dest="pcmd", required=True)

    ap_pcap_decode = pcap_sub.add_parser("decode", help="Decode PCAP file and extract message payloads")
    ap_pcap_decode.add_argument("--pcap", required=True, 
                               help="PCAP file path (supports .pcap, .pcapng, and .txt files)")
    ap_pcap_decode.add_argument("--out", required=True, 
                               help="Output directory path (will be created if it doesn't exist)")
    ap_pcap_decode.set_defaults(func=cmd_pcap_decode)

    # stream subcommand
    ap_stream = sub.add_parser("stream", help="Real-time message streaming via ZeroMQ PUB/SUB pattern")
    stream_sub = ap_stream.add_subparsers(dest="stream_cmd", required=True)

    # stream pub subcommand
    ap_stream_pub = stream_sub.add_parser("pub", help="Publish messages to ZeroMQ PUB socket")
    ap_stream_pub.add_argument("--in", dest="files", nargs="+", required=True, 
                              help="Input file paths (supports glob patterns)")
    ap_stream_pub.add_argument("--format", choices=["cot", "vmf"], required=True, 
                              help="Message format: 'cot' for XML, 'vmf' for binary")
    ap_stream_pub.add_argument("--bind", default="tcp://*:5555", 
                              help="Bind address for ZeroMQ socket (default: tcp://*:5555)")
    ap_stream_pub.add_argument("--delay", type=float, default=1.0, 
                              help="Delay between messages in seconds (default: 1.0)")
    ap_stream_pub.add_argument("--stream", action="store_true", 
                              help="Enable continuous streaming mode (loops through files)")
    ap_stream_pub.set_defaults(func=cmd_stream_pub)

    # stream sub subcommand
    ap_stream_sub = stream_sub.add_parser("sub", help="Subscribe to ZeroMQ PUB socket")
    ap_stream_sub.add_argument("--connect", default="tcp://localhost:5555", 
                              help="Connect address for ZeroMQ socket (default: tcp://localhost:5555)")
    ap_stream_sub.add_argument("--topics", nargs="*", default=["tactical"], 
                              help="Topics to subscribe to (default: tactical)")
    ap_stream_sub.add_argument("--timeout", type=float, 
                              help="Timeout in seconds (optional, runs indefinitely if not specified)")
    # api subcommand
    ap_api = sub.add_parser("api", help="Start REST API server")
    ap_api.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    ap_api.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    ap_api.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    ap_api.set_defaults(func=cmd_api)

    # interactive subcommand
    ap_interactive = sub.add_parser("interactive", help="Start interactive shell for exploration")
    ap_interactive.set_defaults(func=cmd_interactive)

    # status subcommand
    ap_status = sub.add_parser("status", help="Show system status and configuration")
    ap_status.set_defaults(func=cmd_status)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
