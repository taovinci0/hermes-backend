"""Tests for temperature unit conversions.

Stage 1 implementation.
"""

import pytest
from core.units import (
    kelvin_to_celsius,
    celsius_to_fahrenheit,
    kelvin_to_fahrenheit,
    fahrenheit_to_celsius,
    celsius_to_kelvin,
    fahrenheit_to_kelvin,
    resolve_to_whole_f,
)


def test_kelvin_to_celsius() -> None:
    """Test Kelvin to Celsius conversion."""
    assert kelvin_to_celsius(273.15) == pytest.approx(0.0, abs=1e-6)
    assert kelvin_to_celsius(373.15) == pytest.approx(100.0, abs=1e-6)
    assert kelvin_to_celsius(0.0) == pytest.approx(-273.15, abs=1e-6)


def test_celsius_to_fahrenheit() -> None:
    """Test Celsius to Fahrenheit conversion."""
    assert celsius_to_fahrenheit(0.0) == pytest.approx(32.0, abs=1e-6)
    assert celsius_to_fahrenheit(100.0) == pytest.approx(212.0, abs=1e-6)
    assert celsius_to_fahrenheit(-40.0) == pytest.approx(-40.0, abs=1e-6)


def test_kelvin_to_fahrenheit() -> None:
    """Test Kelvin to Fahrenheit conversion."""
    assert kelvin_to_fahrenheit(273.15) == pytest.approx(32.0, abs=1e-6)
    assert kelvin_to_fahrenheit(373.15) == pytest.approx(212.0, abs=1e-6)


def test_fahrenheit_to_celsius() -> None:
    """Test Fahrenheit to Celsius conversion."""
    assert fahrenheit_to_celsius(32.0) == pytest.approx(0.0, abs=1e-6)
    assert fahrenheit_to_celsius(212.0) == pytest.approx(100.0, abs=1e-6)


def test_celsius_to_kelvin() -> None:
    """Test Celsius to Kelvin conversion."""
    assert celsius_to_kelvin(0.0) == pytest.approx(273.15, abs=1e-6)
    assert celsius_to_kelvin(100.0) == pytest.approx(373.15, abs=1e-6)


def test_fahrenheit_to_kelvin() -> None:
    """Test Fahrenheit to Kelvin conversion."""
    assert fahrenheit_to_kelvin(32.0) == pytest.approx(273.15, abs=1e-6)
    assert fahrenheit_to_kelvin(212.0) == pytest.approx(373.15, abs=1e-6)


def test_resolve_to_whole_f() -> None:
    """Test rounding to whole °F (WU/NWS convention).

    Values >= 0.5 round up, < 0.5 round down.
    """
    # Round down
    assert resolve_to_whole_f(59.4) == 59
    assert resolve_to_whole_f(59.49) == 59

    # Round up (>= 0.5)
    assert resolve_to_whole_f(59.5) == 60
    assert resolve_to_whole_f(59.6) == 60
    assert resolve_to_whole_f(60.0) == 60

    # Edge cases
    assert resolve_to_whole_f(0.0) == 0
    assert resolve_to_whole_f(0.5) == 1
    assert resolve_to_whole_f(-0.5) == 0  # -0.5 + 0.5 = 0


def test_roundtrip_conversions() -> None:
    """Test roundtrip conversions maintain accuracy."""
    # K -> C -> K
    temp_k = 298.15
    assert celsius_to_kelvin(kelvin_to_celsius(temp_k)) == pytest.approx(temp_k, abs=1e-6)

    # F -> C -> F
    temp_f = 72.0
    assert celsius_to_fahrenheit(fahrenheit_to_celsius(temp_f)) == pytest.approx(
        temp_f, abs=1e-6
    )

    # K -> F -> K
    temp_k = 293.15
    assert fahrenheit_to_kelvin(kelvin_to_fahrenheit(temp_k)) == pytest.approx(temp_k, abs=1e-6)

