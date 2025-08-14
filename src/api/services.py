"""
Service layer for the Interoperability Messaging Lab API.
Handles business logic for message processing, streaming, and PCAP operations.
"""

import base64
import csv
import io
import json
from pathlib import Path
from typing import Any, Union

# Import our existing business logic
try:
    from ..binutils.pcap_extract import decode_pcap_payloads
    from ..parsers.cot_parser import parse_cot_xml
    from ..parsers.vmf_parser import parse_vmf_binary
    from ..stream.pub import create_publisher
    from ..transforms.normalize_schema import normalize_message
except ImportError:
    # Fallback for when running as package
    from binutils.pcap_extract import decode_pcap_payloads  # type: ignore
    from parsers.cot_parser import parse_cot_xml  # type: ignore
    from parsers.vmf_parser import parse_vmf_binary  # type: ignore
    from stream.pub import create_publisher  # type: ignore
    from transforms.normalize_schema import normalize_message  # type: ignore


class MessageService:
    """Service for message parsing and normalization."""

    def parse_cot(self, content: bytes) -> dict[str, Any]:
        """Parse CoT XML content."""
        return parse_cot_xml(content)

    def parse_vmf(self, content: bytes) -> dict[str, Any]:
        """Parse VMF binary content."""
        return parse_vmf_binary(content)

    def normalize_message(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Normalize parsed message to standard schema."""
        return normalize_message(parsed)

    def convert_format(self, normalized: dict[str, Any], output_format: str) -> Any:
        """Convert normalized message to requested output format."""
        if output_format == "json":
            return normalized
        elif output_format == "ndjson":
            # Convert to NDJSON format
            return self._to_ndjson([normalized])
        elif output_format == "csv":
            # Convert to CSV format
            return self._to_csv([normalized])
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _to_ndjson(self, messages: list[dict[str, Any]]) -> str:
        """Convert messages to NDJSON format."""
        lines = []
        for msg in messages:
            lines.append(json.dumps(msg))
        return "\n".join(lines)

    def _to_csv(self, messages: list[dict[str, Any]]) -> str:
        """Convert messages to CSV format."""
        if not messages:
            return ""

        # Flatten the first message to get headers
        flattened = self._flatten_message(messages[0])
        headers = list(flattened.keys())

        # Create CSV output
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for msg in messages:
            flattened = self._flatten_message(msg)
            writer.writerow(flattened)

        return output.getvalue()

    def _flatten_message(self, message: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten nested message structure for CSV export."""
        flattened = {}

        for key, value in message.items():
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                nested = self._flatten_message(value, f"{prefix}{key}_" if prefix else f"{key}_")
                flattened.update(nested)
            elif isinstance(value, list):
                # Handle lists by joining with semicolons
                flattened[f"{prefix}{key}"] = "; ".join(str(item) for item in value)
            else:
                # Simple value
                flattened[f"{prefix}{key}"] = value

        return flattened


class StreamingService:
    """Service for ZeroMQ message streaming."""

    def __init__(self) -> None:
        self.publishers: dict[str, Any] = {}  # Cache publishers by address

    def publish_message(self, message: dict[str, Any], topic: str = "tactical", delay_ms: int = 1000) -> None:
        """Publish a message to ZeroMQ topic."""
        try:
            # Use default publisher address
            publisher = self._get_publisher("tcp://*:5555")

            # Publish message with topic
            publisher.publish_message(message, topic)

            # Apply delay if specified
            if delay_ms > 0:
                import time
                time.sleep(delay_ms / 1000.0)

        except Exception as e:
            print(f"Error publishing message: {e}")

    def _get_publisher(self, address: str) -> Any:
        """Get or create a publisher for the given address."""
        if address not in self.publishers:
            self.publishers[address] = create_publisher(address)
        return self.publishers[address]

    def close_all(self) -> None:
        """Close all publishers."""
        for publisher in self.publishers.values():
            try:
                publisher.close()
            except Exception:
                pass
        self.publishers.clear()


class PCAPService:
    """Service for PCAP processing."""

    def extract_payloads(self, pcap_path: str) -> list[dict[str, Any]]:
        """Extract payloads from PCAP file."""
        # Create temporary output directory
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract payloads
            decode_pcap_payloads(Path(pcap_path), temp_path)

            # Read extracted files
            payloads = []
            for file_path in temp_path.glob("*"):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        payloads.append({
                            "filename": file_path.name,
                            "size_bytes": len(content),
                            "content": base64.b64encode(content).decode('utf-8'),
                            "content_type": self._detect_content_type(content)
                        })

            return payloads

    def convert_payloads(self, payloads: list[dict[str, Any]], output_format: str) -> Union[list[dict[str, Any]], str]:
        """Convert payloads to requested output format."""
        if output_format == "json":
            return payloads
        elif output_format == "ndjson":
            return self._payloads_to_ndjson(payloads)
        elif output_format == "csv":
            return self._payloads_to_csv(payloads)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _payloads_to_ndjson(self, payloads: list[dict[str, Any]]) -> str:
        """Convert payloads to NDJSON format."""
        lines = []
        for payload in payloads:
            lines.append(json.dumps(payload))
        return "\n".join(lines)

    def _payloads_to_csv(self, payloads: list[dict[str, Any]]) -> str:
        """Convert payloads to CSV format."""
        if not payloads:
            return ""

        # Get headers from first payload
        headers = list(payloads[0].keys())

        # Create CSV output
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for payload in payloads:
            writer.writerow(payload)

        return output.getvalue()

    def _detect_content_type(self, content: bytes) -> str:
        """Detect content type based on content."""
        if content.startswith(b'<'):
            return "xml"
        elif content.startswith(b'{') or content.startswith(b'['):
            return "json"
        elif len(content) > 4 and content[:4] in [b'COT\x00', b'VMF\x00']:
            return "binary"
        else:
            return "unknown"
