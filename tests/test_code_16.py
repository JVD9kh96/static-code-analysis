"""Tests for genCodes.code_16 (Table)."""
import pytest
from genCodes import code_16


def test_table_insert_and_count():
    t = code_16.Table("users", ["id", "name"])
    t.insert([1, "Alice"])
    t.insert([2, "Bob"])
    assert t.count() == 2


def test_table_select_where():
    t = code_16.Table("users", ["id", "name", "role"])
    t.insert([1, "Alice", "admin"])
    t.insert([2, "Bob", "user"])
    t.insert([3, "Carol", "admin"])
    result = t.where(lambda row: row[2] == "admin")
    assert result.count() == 2


def test_table_join():
    emp = code_16.Table("emp", ["id", "name"])
    sal = code_16.Table("sal", ["id", "salary"])
    emp.insert([1, "Alice"])
    emp.insert([2, "Bob"])
    sal.insert([1, 5000])
    sal.insert([2, 4000])
    joined = emp.join(sal, "id")
    assert joined.count() == 2
    assert len(joined.columns) == 3


def test_table_insert_wrong_length():
    t = code_16.Table("users", ["id", "name"])
    with pytest.raises(ValueError, match="Row data length"):
        t.insert([1, "Alice", "extra"])
