"""
Export normalized messages to various formats.
"""

import csv
import json
from pathlib import Path
from typing import Any, TextIO, Union


def to_ndjson(messages: list[dict[str, Any]], output: Union[str, Path, TextIO]) -> int:
    """
    Export normalized messages to NDJSON (Newline Delimited JSON) format.

    Args:
        messages: List of normalized message dictionaries
        output: Output file path or file-like object

    Returns:
        Number of messages exported

    Example:
        >>> messages = [{"id": "1", "type": "test"}, {"id": "2", "type": "test2"}]
        >>> to_ndjson(messages, "output.ndjson")
        2
    """
    count = 0

    if isinstance(output, (str, Path)):
        with open(output, 'w', encoding='utf-8') as f:
            count = _write_ndjson(messages, f)
    else:
        count = _write_ndjson(messages, output)

    return count


def _write_ndjson(messages: list[dict[str, Any]], file_obj: TextIO) -> int:
    """Write messages to NDJSON format in the given file object."""
    count = 0
    for message in messages:
        json.dump(message, file_obj, ensure_ascii=False)
        file_obj.write('\n')
        count += 1
    return count


def to_csv(messages: list[dict[str, Any]], output: Union[str, Path, TextIO]) -> int:
    """
    Export normalized messages to CSV format.

    Args:
        messages: List of normalized message dictionaries
        output: Output file path or file-like object

    Returns:
        Number of messages exported

    Note:
        CSV export flattens nested structures and may lose some data complexity.
        Position and time fields are flattened to individual columns.
    """
    if not messages:
        return 0

    count = 0

    if isinstance(output, (str, Path)):
        with open(output, 'w', newline='', encoding='utf-8') as f:
            count = _write_csv(messages, f)
    else:
        count = _write_csv(messages, output)

    return count


def _write_csv(messages: list[dict[str, Any]], file_obj: TextIO) -> int:
    """Write messages to CSV format in the given file object."""
    if not messages:
        return 0

    # Flatten the nested structure for CSV
    flattened_messages = []
    for msg in messages:
        flat = {
            'schema_version': msg.get('schema_version'),
            'source_format': msg.get('source_format'),
            'id': msg.get('id'),
            'type': msg.get('type'),
            'how': msg.get('how'),
            'time_reported': msg.get('time', {}).get('reported'),
            'time_start': msg.get('time', {}).get('start'),
            'time_stale': msg.get('time', {}).get('stale'),
            'position_lat': msg.get('position', {}).get('lat'),
            'position_lon': msg.get('position', {}).get('lon'),
            'position_hae': msg.get('position', {}).get('hae'),
            'position_ce': msg.get('position', {}).get('ce'),
            'position_le': msg.get('position', {}).get('le'),
        }

        # Add detail fields (flattened)
        detail = msg.get('detail', {})
        for key, value in detail.items():
            flat[f'detail_{key}'] = value

        flattened_messages.append(flat)

    # Get all possible column names
    all_columns: set[str] = set()
    for msg in flattened_messages:
        all_columns.update(msg.keys())

    # Sort columns for consistent output
    columns = sorted(all_columns)

    writer = csv.DictWriter(file_obj, fieldnames=columns)
    writer.writeheader()

    count = 0
    for msg in flattened_messages:
        # Ensure all columns are present (fill missing with None)
        row = {col: msg.get(col) for col in columns}
        writer.writerow(row)
        count += 1

    return count


def export_messages(
    messages: list[dict[str, Any]],
    output: Union[str, Path],
    format_type: str = "json"
) -> int:
    """
    Export messages in the specified format.

    Args:
        messages: List of normalized message dictionaries
        output: Output file path
        format_type: Export format ("json", "ndjson", "csv")

    Returns:
        Number of messages exported

    Raises:
        ValueError: If format_type is not supported
    """
    format_type = format_type.lower()

    if format_type == "json":
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        return len(messages)
    elif format_type == "ndjson":
        return to_ndjson(messages, output)
    elif format_type == "csv":
        return to_csv(messages, output)
    else:
        raise ValueError(f"Unsupported format: {format_type}. Use 'json', 'ndjson', or 'csv'")
