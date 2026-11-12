"""ID generation utilities."""

from uuid import uuid4


def generate_id() -> str:
    """Generate a new unique ID as a hex string."""
    return uuid4().hex
