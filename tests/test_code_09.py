"""Tests for genCodes.code_09 (BinarySearchTree)."""
import pytest
from genCodes import code_09


def test_bst_insert_and_search():
    bst = code_09.BinarySearchTree()
    for v in [5, 3, 7, 2, 4, 6, 8]:
        bst.insert(v)
    assert bst.search(4) is True
    assert bst.search(9) is False


def test_bst_inorder_traversal():
    bst = code_09.BinarySearchTree()
    for v in [5, 3, 7, 2, 4, 6, 8]:
        bst.insert(v)
    assert bst.inorder_traversal() == [2, 3, 4, 5, 6, 7, 8]


def test_bst_height():
    bst = code_09.BinarySearchTree()
    assert bst.height() == -1
    bst.insert(5)
    assert bst.height() == 0
    bst.insert(3)
    bst.insert(7)
    assert bst.height() == 1
