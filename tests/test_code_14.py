"""Tests for genCodes.code_14 (Observer, Subject, StockMarket)."""
import pytest
from genCodes import code_14


def test_subject_attach_detach_notify():
    subject = code_14.Subject()
    observed = []

    class TestObserver(code_14.Observer):
        def update(self, event_data):
            observed.append(event_data)

    obs = TestObserver()
    subject.attach(obs)
    subject.set_state("hello")
    assert "hello" in observed
    subject.detach(obs)
    subject.set_state("world")
    assert observed.count("world") == 0


def test_stock_market_update_price():
    market = code_14.StockMarket("AAPL")
    assert market.price == 0
    market.update_price(150.0)
    assert market.price == 150.0
    market.update_price(152.5)
    assert market.price == 152.5
