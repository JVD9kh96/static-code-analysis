"""Tests for genCodes.code_13 (FileSystem, File, Directory)."""
import pytest
from genCodes import code_13


def test_file_get_size():
    f = code_13.File("test.txt", 1024)
    assert f.get_size() == 1024


def test_directory_add_child_and_size():
    d = code_13.Directory("docs")
    d.add_child(code_13.File("a.txt", 100))
    d.add_child(code_13.File("b.txt", 200))
    assert d.get_size() == 300
    assert set(d.list_contents()) == {"a.txt", "b.txt"}


def test_file_system_create_file_and_total_size():
    fs = code_13.FileSystem()
    fs.create_file("/documents/file1.txt", 1024)
    fs.create_file("/documents/file2.txt", 2048)
    assert fs.get_total_size() == 3072
    assert "documents" in fs.root.list_contents()
