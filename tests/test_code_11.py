"""Tests for genCodes.code_11 (Graph)."""
import pytest
from genCodes import code_11


def test_graph_add_edge_and_neighbors():
    g = code_11.Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    neighbors = g.get_neighbors("A")
    assert len(neighbors) == 2
    assert any(n[0] == "B" for n in neighbors)
    assert any(n[0] == "C" for n in neighbors)


def test_graph_dfs():
    g = code_11.Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    g.add_edge("C", "D")
    result = g.dfs("A")
    assert "A" in result
    assert len(result) == 4


def test_graph_bfs():
    g = code_11.Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    result = g.bfs("A")
    assert result[0] == "A"
    assert set(result) == {"A", "B", "C", "D"}


def test_graph_shortest_path():
    g = code_11.Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")
    g.add_edge("C", "D")
    path = g.shortest_path("A", "D")
    assert path is not None
    assert path[0] == "A" and path[-1] == "D"
