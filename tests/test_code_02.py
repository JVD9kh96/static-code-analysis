"""Tests for genCodes.code_02 (Student)."""
import pytest
from genCodes import code_02


def test_student_add_grade_and_average():
    student = code_02.Student("Alice", 20, "S001")
    student.add_grade(80)
    student.add_grade(100)
    assert student.get_average() == 90.0


def test_student_empty_grades_average():
    student = code_02.Student("Bob", 22, "S002")
    assert student.get_average() == 0


def test_student_get_info():
    student = code_02.Student("Carol", 21, "S003")
    student.add_grade(90)
    info = student.get_info()
    assert "Carol" in info and "S003" in info
