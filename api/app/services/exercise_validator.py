"""Exercise measurement validation service."""

# Measurement schema: defines valid measurement types and their constraints
MEASUREMENT_SCHEMA = {
    "duration": {
        "type": "integer",
        "unit": "seconds",
        "min": 0,
        "description": "Duration in seconds",
    },
    "reps": {
        "type": "integer",
        "unit": "count",
        "min": 1,
        "description": "Number of repetitions",
    },
    "jumps": {
        "type": "integer",
        "unit": "count",
        "min": 1,
        "description": "Number of jumps",
    },
    "distance": {
        "type": "number",
        "unit": "km",
        "min": 0,
        "description": "Distance in kilometers",
    },
    "sets": {
        "type": "integer",
        "unit": "count",
        "min": 1,
        "description": "Number of sets",
    },
    "weight": {
        "type": "number",
        "unit": "kg",
        "min": 0,
        "description": "Weight in kilograms",
    },
}

VALID_MEASUREMENTS = set(MEASUREMENT_SCHEMA.keys())


def validate_measurements(measurements: dict, allowed_measurements: list = None) -> tuple[bool, str | None]:
    """
    Validate measurements dictionary against schema and allowed measurements.

    Args:
        measurements: Dictionary of measurement values (e.g., {"duration": 1800, "reps": 10})
        allowed_measurements: List of allowed measurement types for this exercise (None = all allowed)

    Returns:
        (is_valid, error_message) tuple
    """
    if not isinstance(measurements, dict):
        return False, "Measurements must be a dictionary"

    for key, value in measurements.items():
        # Check if measurement type is valid
        if key not in MEASUREMENT_SCHEMA:
            return False, f"Invalid measurement type: {key}"

        # Check if measurement is allowed for this exercise
        if allowed_measurements is not None and key not in allowed_measurements:
            return False, f"Measurement '{key}' is not allowed for this exercise"

        # Validate value type and constraints
        schema = MEASUREMENT_SCHEMA[key]

        if value is None:
            continue  # Allow null values

        if schema["type"] == "integer":
            # Accept floats that are whole numbers (e.g., 30.0 from HTML number inputs)
            if isinstance(value, float) and value == int(value):
                measurements[key] = int(value)
                value = measurements[key]
            elif not isinstance(value, int) or isinstance(value, bool):
                return False, f"{key} must be an integer"
        elif schema["type"] == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"{key} must be a number"

        # Check min constraint
        if "min" in schema and value < schema["min"]:
            return False, f"{key} must be at least {schema['min']}"

    return True, None


def validate_allowed_measurements(allowed_measurements: list) -> tuple[bool, str | None]:
    """
    Validate that allowed_measurements list contains only valid measurement types.

    Args:
        allowed_measurements: List of measurement types

    Returns:
        (is_valid, error_message) tuple
    """
    if not isinstance(allowed_measurements, list):
        return False, "allowed_measurements must be a list"

    if len(allowed_measurements) == 0:
        return False, "At least one measurement type must be allowed"

    for measurement in allowed_measurements:
        if measurement not in VALID_MEASUREMENTS:
            return False, f"Invalid measurement type: {measurement}. Valid types: {', '.join(VALID_MEASUREMENTS)}"

    return True, None


def get_measurement_schema() -> dict:
    """Get the complete measurement schema for API responses."""
    return MEASUREMENT_SCHEMA
