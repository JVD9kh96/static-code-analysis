"""Tests for genCodes.code_04 (Book, Library)."""
import pytest
from genCodes import code_04


def test_book_borrow_and_return():
    book = code_04.Book("Python Basics", "John Doe", "ISBN001")
    assert book.is_available is True
    book.borrow()
    assert book.is_available is False
    book.return_book()
    assert book.is_available is True


def test_library_add_and_find_book():
    library = code_04.Library()
    book = code_04.Book("Advanced Python", "Jane Smith", "ISBN002")
    library.add_book(book)
    found = library.find_book("ISBN002")
    assert found is book
    assert library.find_book("ISBN999") is None


def test_library_list_available_books():
    library = code_04.Library()
    book1 = code_04.Book("A", "Author", "1")
    book2 = code_04.Book("B", "Author", "2")
    library.add_book(book1)
    library.add_book(book2)
    book1.borrow()
    available = library.list_available_books()
    assert len(available) == 1
    assert available[0].title == "B"
