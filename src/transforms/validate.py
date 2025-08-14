"""
Schema validation for normalized tactical messages.
"""

import json
from pathlib import Path

try:
    from jsonschema import ValidationError, validate
    from jsonschema.validators import Draft202012Validator
except ImportError:
    # Graceful fallback if jsonschema is not available
    validate = None
    ValidationError = Exception
    Draft202012Validator = None


def _load_schema() -> dict:
    """Load the normalized message schema from the schema directory."""
    schema_path = Path(__file__).parent.parent.parent / "schema" / "normalized_message.schema.json"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path) as f:
        return json.load(f)


def validate_normalized(obj: dict) -> bool:
    """
    Validate a normalized message object against the schema.

    Args:
        obj: The normalized message object to validate

    Returns:
        True if valid, raises ValidationError if invalid

    Raises:
        ValidationError: If the object doesn't match the schema
        ImportError: If jsonschema is not available
    """
    if validate is None:
        raise ImportError("jsonschema package is required for validation")

    schema = _load_schema()
    validate(instance=obj, schema=schema, cls=Draft202012Validator)
    return True


def validate_and_raise(obj: dict) -> None:
    """
    Validate a normalized message object and raise an exception if invalid.

    Args:
        obj: The normalized message object to validate

    Raises:
        ValidationError: If the object doesn't match the schema
        ImportError: If jsonschema is not available
    """
    validate_normalized(obj)


def is_valid(obj: dict) -> bool:
    """
    Check if a normalized message object is valid without raising exceptions.

    Args:
        obj: The normalized message object to validate

    Returns:
        True if valid, False if invalid or validation unavailable
    """
    try:
        return validate_normalized(obj)
    except (ValidationError, ImportError):
        return False
