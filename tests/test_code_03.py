"""Tests for genCodes.code_03 (BankAccount)."""
import pytest
from genCodes import code_03


def test_bank_account_deposit_and_balance():
    account = code_03.BankAccount("ACC001", 1000)
    account.deposit(500)
    assert account.get_balance() == 1500
    assert account.get_transaction_count() == 1


def test_bank_account_withdraw():
    account = code_03.BankAccount("ACC002", 1000)
    account.withdraw(200)
    assert account.get_balance() == 800
    assert account.get_transaction_count() == 1


def test_bank_account_invalid_deposit():
    account = code_03.BankAccount("ACC003", 100)
    account.deposit(-50)
    assert account.get_balance() == 100


def test_bank_account_insufficient_funds():
    account = code_03.BankAccount("ACC004", 100)
    account.withdraw(200)
    assert account.get_balance() == 100
