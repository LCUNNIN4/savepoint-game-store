"""Small helpers shared by all the route files."""
from flask import request


class ApiError(Exception):
    """An API failure with a message and HTTP status."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def get_json():
    """Return the JSON body of the request as a dictionary."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be JSON")
    return data


def require_text(data, field, max_len):
    """Read a required text field, trimmed. Error if missing or too long."""
    value = str(data.get(field) or "").strip()
    if not value:
        raise ApiError(f"'{field}' is required")
    if len(value) > max_len:
        raise ApiError(f"'{field}' must be at most {max_len} characters")
    return value


def optional_text(data, field, max_len):
    """Read an optional text field. Empty text is stored as NULL."""
    value = str(data.get(field) or "").strip()
    if len(value) > max_len:
        raise ApiError(f"'{field}' must be at most {max_len} characters")
    return value or None


def require_int(data, field, minimum=0):
    """Read a required whole number that is at least `minimum`."""
    value = data.get(field)
    try:
        if isinstance(value, bool) or (isinstance(value, float) and value != int(value)):
            raise ValueError
        number = int(value)
    except (TypeError, ValueError):
        raise ApiError(f"'{field}' must be a whole number")
    if number < minimum:
        raise ApiError(f"'{field}' must be at least {minimum}")
    return number
