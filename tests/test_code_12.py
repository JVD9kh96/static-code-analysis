"""Tests for genCodes.code_12 (LRUCache)."""
import pytest
from genCodes import code_12


def test_lru_cache_put_and_get():
    cache = code_12.LRUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get("a") == 1
    assert cache.get("b") == 2
    assert cache.size() == 3


def test_lru_cache_eviction():
    cache = code_12.LRUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    cache.put("d", 4)
    assert cache.get("a") is None
    assert cache.get("d") == 4
    assert cache.size() == 3


def test_lru_cache_remove_and_clear():
    cache = code_12.LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.remove("a")
    assert cache.get("a") is None
    assert cache.size() == 1
    cache.clear()
    assert cache.size() == 0
