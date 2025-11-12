"""Unit conversion utilities for temperature.

Handles Kelvin ↔ Celsius ↔ Fahrenheit conversions and "resolve to whole °F" rounding.
"""


def kelvin_to_celsius(temp_k: float) -> float:
    """Convert Kelvin to Celsius.

    Args:
        temp_k: Temperature in Kelvin

    Returns:
        Temperature in Celsius
    """
    return temp_k - 273.15


def celsius_to_fahrenheit(temp_c: float) -> float:
    """Convert Celsius to Fahrenheit.

    Args:
        temp_c: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit
    """
    return (temp_c * 9.0 / 5.0) + 32.0


def kelvin_to_fahrenheit(temp_k: float) -> float:
    """Convert Kelvin to Fahrenheit.

    Args:
        temp_k: Temperature in Kelvin

    Returns:
        Temperature in Fahrenheit
    """
    return celsius_to_fahrenheit(kelvin_to_celsius(temp_k))


def fahrenheit_to_celsius(temp_f: float) -> float:
    """Convert Fahrenheit to Celsius.

    Args:
        temp_f: Temperature in Fahrenheit

    Returns:
        Temperature in Celsius
    """
    return (temp_f - 32.0) * 5.0 / 9.0


def celsius_to_kelvin(temp_c: float) -> float:
    """Convert Celsius to Kelvin.

    Args:
        temp_c: Temperature in Celsius

    Returns:
        Temperature in Kelvin
    """
    return temp_c + 273.15


def fahrenheit_to_kelvin(temp_f: float) -> float:
    """Convert Fahrenheit to Kelvin.

    Args:
        temp_f: Temperature in Fahrenheit

    Returns:
        Temperature in Kelvin
    """
    return celsius_to_kelvin(fahrenheit_to_celsius(temp_f))


def resolve_to_whole_f(temp_f: float) -> int:
    """Round temperature to nearest whole °F (WU/NWS convention).

    Weather Underground and NWS report whole °F values. For resolution:
    - Values < 0.5 round down
    - Values >= 0.5 round up

    Args:
        temp_f: Temperature in Fahrenheit

    Returns:
        Rounded temperature as integer °F
    """
    return int(temp_f + 0.5)

