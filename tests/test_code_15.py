"""Tests for genCodes.code_15 (SortingAlgorithms, SortPerformanceTracker)."""
import pytest
from genCodes import code_15


def test_bubble_sort():
    arr = [64, 34, 25, 12, 22, 11, 90, 5]
    result = code_15.SortingAlgorithms.bubble_sort(arr)
    assert result == sorted(arr)
    assert arr == [64, 34, 25, 12, 22, 11, 90, 5]


def test_quick_sort():
    arr = [3, 6, 8, 10, 1, 2, 1]
    result = code_15.SortingAlgorithms.quick_sort(arr)
    assert result == sorted(arr)


def test_merge_sort():
    arr = [38, 27, 43, 3, 9, 82, 10]
    result = code_15.SortingAlgorithms.merge_sort(arr)
    assert result == sorted(arr)


def test_insertion_sort():
    arr = [12, 11, 13, 5, 6]
    result = code_15.SortingAlgorithms.insertion_sort(arr)
    assert result == sorted(arr)


def test_sort_performance_tracker():
    tracker = code_15.SortPerformanceTracker()
    data = [5, 2, 8, 1, 9]
    result = tracker.benchmark("Quick Sort", code_15.SortingAlgorithms.quick_sort, data)
    assert result == sorted(data)
    assert "Quick Sort" in tracker.results
    assert tracker.results["Quick Sort"]["sorted"] is True
