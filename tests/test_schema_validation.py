"""
Tests for schema validation of normalized messages.
"""

import pytest

from src.parsers.cot_parser import parse_cot_xml
from src.parsers.vmf_parser import parse_vmf_binary
from src.transforms.normalize_schema import normalize_message
from src.transforms.validate import (
    ValidationError,
    is_valid,
    validate_and_raise,
    validate_normalized,
)
from tools.make_vmf_sample import make_sample


def test_cot_normalized_validation():
    """Test that CoT normalized messages pass schema validation."""
    sample = b"""
    <event version="2.0" uid="T-123" type="a-f-A" how="m-g"
           time="2025-08-14T12:00:00Z" start="2025-08-14T12:00:00Z" stale="2025-08-14T13:00:00Z">
      <point lat="38.7" lon="-77.2" hae="100.0" ce="30.0" le="10.0"/>
      <detail callsign="VIKING11"/>
    </event>
    """
    parsed = parse_cot_xml(sample)
    norm = normalize_message(parsed)

    # Should pass validation
    assert validate_normalized(norm) is True
    validate_and_raise(norm)  # Should not raise
    assert is_valid(norm) is True


def test_vmf_normalized_validation():
    """Test that VMF normalized messages pass schema validation."""
    sample = make_sample(msg_type=7, lat=38.7, lon=-77.2, ts=1_725_000_000)

    parsed = parse_vmf_binary(sample)
    norm = normalize_message(parsed)

    # Should pass validation
    assert validate_normalized(norm) is True
    validate_and_raise(norm)  # Should not raise
    assert is_valid(norm) is True


def test_invalid_schema_validation():
    """Test that invalid objects fail schema validation."""
    # Missing required fields
    invalid_obj = {
        "schema_version": "1.0",
        "source_format": "cot",
        # Missing: type, time, position
    }

    with pytest.raises((ValidationError, Exception)):  # ValidationError or similar
        validate_normalized(invalid_obj)

    with pytest.raises((ValidationError, Exception)):
        validate_and_raise(invalid_obj)

    assert is_valid(invalid_obj) is False


def test_invalid_source_format():
    """Test that invalid source_format values fail validation."""
    invalid_obj = {
        "schema_version": "1.0",
        "source_format": "invalid_format",  # Not in enum
        "type": "test",
        "time": {"reported": "2025-08-14T12:00:00Z"},
        "position": {"lat": 38.7, "lon": -77.2}
    }

    with pytest.raises((ValidationError, Exception)):
        validate_normalized(invalid_obj)

    assert is_valid(invalid_obj) is False


def test_invalid_schema_version():
    """Test that invalid schema_version values fail validation."""
    invalid_obj = {
        "schema_version": "invalid",  # Doesn't match pattern
        "source_format": "cot",
        "type": "test",
        "time": {"reported": "2025-08-14T12:00:00Z"},
        "position": {"lat": 38.7, "lon": -77.2}
    }

    with pytest.raises((ValidationError, Exception)):
        validate_normalized(invalid_obj)

    assert is_valid(invalid_obj) is False


def test_additional_properties_rejected():
    """Test that additional properties are rejected."""
    invalid_obj = {
        "schema_version": "1.0",
        "source_format": "cot",
        "type": "test",
        "time": {"reported": "2025-08-14T12:00:00Z"},
        "position": {"lat": 38.7, "lon": -77.2},
        "extra_field": "should_not_be_allowed"  # Additional property
    }

    with pytest.raises((ValidationError, Exception)):
        validate_normalized(invalid_obj)

    assert is_valid(invalid_obj) is False


def test_null_values_allowed():
    """Test that null values are allowed for optional fields."""
    valid_obj = {
        "schema_version": "1.0",
        "source_format": "vmf",
        "id": None,
        "type": "vmf:7",
        "how": None,
        "time": {
            "reported": 1_725_000_000,
            "start": None,
            "stale": None
        },
        "position": {
            "lat": 38.7,
            "lon": -77.2,
            "hae": None,
            "ce": None,
            "le": None
        },
        "detail": {}
    }

    assert validate_normalized(valid_obj) is True
    assert is_valid(valid_obj) is True
