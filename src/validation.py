"""
Input validation utilities for user input sanitization and security.
"""

import re
from pathlib import Path

from src.exceptions import ValidationError


def validate_query(query: str, max_length: int = 2000) -> str:
    """
    Validate and sanitize user query input.

    Args:
        query: User input query string
        max_length: Maximum allowed query length

    Returns:
        Sanitized query string

    Raises:
        ValidationError: If query is invalid
    """
    if not query or not query.strip():
        raise ValidationError("Query cannot be empty")

    query = query.strip()

    if len(query) > max_length:
        raise ValidationError(f"Query exceeds maximum length of {max_length} characters")

    # Check for suspicious path traversal patterns
    if re.search(r"\.\.[/\\]", query):
        raise ValidationError("Query contains suspicious path traversal patterns")

    return query


def validate_file_path(path: str | Path, base_dir: Path) -> Path:
    """
    Validate file path is within allowed directory.

    Args:
        path: File path to validate
        base_dir: Base directory that path must be within

    Returns:
        Resolved Path object

    Raises:
        ValidationError: If path is invalid or outside base directory
    """
    try:
        path_obj = Path(path).resolve()
        base_dir = base_dir.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Invalid path: {e}")

    # Check if path is within base directory
    try:
        path_obj.relative_to(base_dir)
    except ValueError:
        raise ValidationError(f"Path must be within {base_dir}, got {path_obj}")

    return path_obj


def validate_positive_integer(value: int, name: str, max_value: int | None = None) -> int:
    """
    Validate that value is a positive integer within bounds.

    Args:
        value: Integer value to validate
        name: Name of the parameter (for error messages)
        max_value: Optional maximum allowed value

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer")

    if value <= 0:
        raise ValidationError(f"{name} must be positive")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{name} cannot exceed {max_value}")

    return value


def validate_model_name(model_name: str) -> str:
    """
    Validate model name format.

    Args:
        model_name: Model name to validate

    Returns:
        Validated model name

    Raises:
        ValidationError: If model name is invalid
    """
    if not model_name or not model_name.strip():
        raise ValidationError("Model name cannot be empty")

    model_name = model_name.strip()

    # Model names should be alphanumeric with hyphens, colons, and underscores
    if not re.match(r"^[a-zA-Z0-9_:\-\.]+$", model_name):
        raise ValidationError(
            "Model name can only contain letters, numbers, hyphens, colons, dots, and underscores"
        )

    return model_name
