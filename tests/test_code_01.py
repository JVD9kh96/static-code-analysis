"""Tests for genCodes.code_01 (Calculator)."""
import pytest
from genCodes import code_01


def test_calculator_add():
    calc = code_01.Calculator()
    assert calc.add(2, 3) == 5
    assert calc.add(-1, 1) == 0


def test_calculator_subtract():
    calc = code_01.Calculator()
    assert calc.subtract(5, 3) == 2
    assert calc.subtract(0, 1) == -1


def test_calculator_multiply():
    calc = code_01.Calculator()
    assert calc.multiply(6, 7) == 42


def test_calculator_divide():
    calc = code_01.Calculator()
    assert calc.divide(20, 5) == 4.0
    assert calc.divide(10, 0) == "Cannot divide by zero"
