"""
Tests for message exporters (NDJSON, CSV).
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from src.transforms.exporters import export_messages, to_csv, to_ndjson


def test_to_ndjson():
    """Test NDJSON export functionality."""
    messages = [
        {"id": "1", "type": "test", "value": 42},
        {"id": "2", "type": "test2", "value": 100}
    ]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.ndjson', delete=False) as f:
        temp_path = f.name

    try:
        count = to_ndjson(messages, temp_path)
        assert count == 2

        # Verify content
        with open(temp_path) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert json.loads(lines[0].strip()) == {"id": "1", "type": "test", "value": 42}
        assert json.loads(lines[1].strip()) == {"id": "2", "type": "test2", "value": 100}

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_to_csv():
    """Test CSV export functionality."""
    messages = [
        {
            "schema_version": "1.0",
            "source_format": "cot",
            "id": "T-123",
            "type": "a-f-A",
            "position": {"lat": 38.7, "lon": -77.2},
            "detail": {"callsign": "VIKING11"}
        },
        {
            "schema_version": "1.0",
            "source_format": "vmf",
            "id": None,
            "type": "vmf:42",
            "position": {"lat": 39.0, "lon": -78.0},
            "detail": {}
        }
    ]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
        temp_path = f.name

    try:
        count = to_csv(messages, temp_path)
        assert count == 2

        # Verify content
        with open(temp_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2

        # Check that nested structures are flattened
        assert 'position_lat' in rows[0]
        assert 'position_lon' in rows[0]
        assert 'detail_callsign' in rows[0]

        # Check first row values
        assert rows[0]['id'] == 'T-123'
        assert rows[0]['position_lat'] == '38.7'
        assert rows[0]['detail_callsign'] == 'VIKING11'

        # Check second row values
        assert rows[1]['id'] == ''
        assert rows[1]['position_lat'] == '39.0'

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_messages_json():
    """Test export_messages with JSON format."""
    messages = [{"id": "1", "type": "test"}]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        count = export_messages(messages, temp_path, "json")
        assert count == 1

        # Verify content
        with open(temp_path) as f:
            data = json.load(f)

        assert data == [{"id": "1", "type": "test"}]

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_messages_ndjson():
    """Test export_messages with NDJSON format."""
    messages = [{"id": "1", "type": "test"}]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.ndjson', delete=False) as f:
        temp_path = f.name

    try:
        count = export_messages(messages, temp_path, "ndjson")
        assert count == 1

        # Verify content
        with open(temp_path) as f:
            lines = f.readlines()

        assert len(lines) == 1
        assert json.loads(lines[0].strip()) == {"id": "1", "type": "test"}

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_messages_csv():
    """Test export_messages with CSV format."""
    messages = [{"id": "1", "type": "test"}]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
        temp_path = f.name

    try:
        count = export_messages(messages, temp_path, "csv")
        assert count == 1

        # Verify content
        with open(temp_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]['id'] == '1'
        assert rows[0]['type'] == 'test'

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_export_messages_invalid_format():
    """Test export_messages with invalid format."""
    messages = [{"id": "1", "type": "test"}]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Unsupported format"):
            export_messages(messages, temp_path, "invalid")

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_csv_flattening():
    """Test that CSV export properly flattens nested structures."""
    messages = [
        {
            "schema_version": "1.0",
            "source_format": "cot",
            "time": {
                "reported": "2025-08-14T12:00:00Z",
                "start": "2025-08-14T12:00:00Z"
            },
            "position": {
                "lat": 38.7,
                "lon": -77.2
            },
            "detail": {
                "callsign": "VIKING11",
                "mission": "PATROL"
            }
        }
    ]

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
        temp_path = f.name

    try:
        count = to_csv(messages, temp_path)
        assert count == 1

        # Verify flattened structure
        with open(temp_path, newline='') as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # Check that nested fields are flattened
        assert 'time_reported' in row
        assert 'time_start' in row
        assert 'position_lat' in row
        assert 'position_lon' in row
        assert 'detail_callsign' in row
        assert 'detail_mission' in row

        # Check values
        assert row['time_reported'] == '2025-08-14T12:00:00Z'
        assert row['position_lat'] == '38.7'
        assert row['detail_callsign'] == 'VIKING11'

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_empty_messages():
    """Test export with empty message list."""
    messages = []

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
        temp_path = f.name

    try:
        count = to_csv(messages, temp_path)
        assert count == 0

        # Verify file exists but is empty (except header)
        with open(temp_path, newline='') as f:
            content = f.read()

        # Should only have header, no data rows
        lines = content.strip().split('\n')
        assert len(lines) == 1  # Just header

    finally:
        Path(temp_path).unlink(missing_ok=True)
