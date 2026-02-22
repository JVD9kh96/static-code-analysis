"""Tests for genCodes.code_10 (Matrix)."""
import pytest
from genCodes import code_10


def test_matrix_add():
    m1 = code_10.Matrix(2, 2, [[1, 2], [3, 4]])
    m2 = code_10.Matrix(2, 2, [[5, 6], [7, 8]])
    m3 = m1 + m2
    assert m3.data == [[6, 8], [10, 12]]


def test_matrix_scalar_multiply():
    m = code_10.Matrix(2, 2, [[1, 2], [3, 4]])
    m2 = m * 2
    assert m2.data == [[2, 4], [6, 8]]


def test_matrix_transpose():
    m = code_10.Matrix(2, 2, [[1, 2], [3, 4]])
    t = m.transpose()
    assert t.rows == 2 and t.cols == 2
    assert t.data == [[1, 3], [2, 4]]


def test_matrix_determinant():
    m = code_10.Matrix(2, 2, [[1, 2], [3, 4]])
    assert m.determinant() == -2


def test_matrix_invalid_dimensions():
    with pytest.raises(ValueError, match="Invalid matrix dimensions"):
        code_10.Matrix(2, 2, [[1, 2, 3], [4, 5, 6]])
