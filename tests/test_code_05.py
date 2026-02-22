"""Tests for genCodes.code_05 (Product, ShoppingCart)."""
import pytest
from genCodes import code_05


def test_shopping_cart_add_and_total():
    cart = code_05.ShoppingCart()
    p1 = code_05.Product("P001", "Laptop", 999.99)
    p2 = code_05.Product("P002", "Mouse", 29.99)
    cart.add_item(p1, 1)
    cart.add_item(p2, 2)
    assert cart.get_total() == pytest.approx(999.99 + 29.99 * 2)
    assert cart.get_item_count() == 3


def test_shopping_cart_remove_item():
    cart = code_05.ShoppingCart()
    p = code_05.Product("P001", "Item", 10.0)
    cart.add_item(p, 2)
    cart.remove_item("P001")
    assert cart.get_total() == 0
    assert cart.get_item_count() == 0


def test_shopping_cart_update_quantity():
    cart = code_05.ShoppingCart()
    p = code_05.Product("P001", "Item", 10.0)
    cart.add_item(p, 2)
    cart.update_quantity("P001", 5)
    assert cart.get_item_count() == 5
    assert cart.get_total() == 50.0
