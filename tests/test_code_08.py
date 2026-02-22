"""Tests for genCodes.code_08 (Employee, Manager, Developer, SalesPerson)."""
import pytest
from genCodes import code_08


def test_employee_calculate_salary():
    emp = code_08.Employee("Alice", "E001", 5000)
    assert emp.calculate_salary() == 5000
    assert "Alice" in emp.get_info()


def test_manager_salary_with_bonus():
    manager = code_08.Manager("Bob", "E002", 5000, 1000)
    assert manager.calculate_salary() == 6000


def test_developer_overtime():
    dev = code_08.Developer("Carol", "E003", 4000, overtime_hours=10)
    assert dev.calculate_salary() == 4100
    dev.add_overtime(5)
    assert dev.calculate_salary() == 4150


def test_salesperson_commission():
    sales = code_08.SalesPerson("Dave", "E004", 3000, commission_rate=0.1)
    sales.add_sale(10000)
    assert sales.calculate_salary() == 4000
