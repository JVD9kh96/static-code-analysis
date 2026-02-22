"""Tests for genCodes.code_17 (ExpressionEvaluator, ExpressionValidator)."""
import pytest
from genCodes import code_17


def test_expression_evaluator():
    ev = code_17.ExpressionEvaluator()
    assert ev.evaluate("2 + 3") == pytest.approx(5)
    assert ev.evaluate("2 + 3 * 4") == pytest.approx(14)
    assert ev.evaluate("(2 + 3) * 4") == pytest.approx(20)


def test_expression_validator_valid():
    valid, msg = code_17.ExpressionValidator.validate("2 + 3 * 4")
    assert valid is True
    assert "Valid" in msg


def test_expression_validator_unmatched_parens():
    valid, _ = code_17.ExpressionValidator.validate("(2 + 3")
    assert valid is False
    valid, _ = code_17.ExpressionValidator.validate("2 + 3)")
    assert valid is False


def test_expression_validator_empty():
    valid, _ = code_17.ExpressionValidator.validate("")
    assert valid is False
