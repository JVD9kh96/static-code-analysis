"""Tests for genCodes.code_06 (TemperatureConverter, Temperature)."""
import pytest
from genCodes import code_06


def test_temperature_converter_celsius_fahrenheit():
    assert code_06.TemperatureConverter.celsius_to_fahrenheit(0) == 32
    assert code_06.TemperatureConverter.celsius_to_fahrenheit(100) == 212


def test_temperature_converter_fahrenheit_celsius():
    assert code_06.TemperatureConverter.fahrenheit_to_celsius(32) == 0
    assert code_06.TemperatureConverter.celsius_to_kelvin(0) == pytest.approx(273.15)


def test_temperature_class_conversion():
    temp = code_06.Temperature(25, "celsius")
    assert temp.to_celsius() == 25
    assert temp.to_fahrenheit() == pytest.approx(77.0)
    assert temp.to_kelvin() == pytest.approx(298.15)


def test_temperature_invalid_unit():
    with pytest.raises(ValueError, match="Invalid unit"):
        code_06.Temperature(25, "invalid")
