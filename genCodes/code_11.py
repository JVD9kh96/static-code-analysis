
class Graph:
    """Graph implementation using adjacency list."""

    def __init__(self):
        """Initialize the graph with an empty adjacency list."""
        self.adjacency_list = {}

    def add_vertex(self, vertex):
        """Add a vertex to the graph."""
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = []

    def add_edge(self, vertex1, vertex2, weight=1):
        """Add an edge between two vertices."""
        if vertex1 not in self.adjacency_list:
            self.add_vertex(vertex1)
        if vertex2 not in self.adjacency_list:
            self.add_vertex(vertex2)
        self.adjacency_list[vertex1].append((vertex2, weight))
        self.adjacency_list[vertex2].append((vertex1, weight))

    def get_neighbors(self, vertex):
        """Get neighbors of a vertex."""
        return self.adjacency_list.get(vertex, [])

    def dfs(self, start, visited=None):
        """Depth-first search traversal."""
        if visited is None:
            visited = set()
        visited.add(start)
        result = [start]
        for neighbor, _ in self.get_neighbors(start):
            if neighbor not in visited:
                result.extend(self.dfs(neighbor, visited))
        return result

    def bfs(self, start):
        """Breadth-first search traversal."""
        visited = set()
        queue = [start]
        result = []
        visited.add(start)
        while queue:
            vertex = queue.pop(0)
            result.append(vertex)
            for neighbor, _ in self.get_neighbors(vertex):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return result

    def shortest_path(self, start, end):
        """Find shortest path using BFS."""
        if start == end:
            return [start]
        visited = set()
        queue = [(start, [start])]
        visited.add(start)
        while queue:
            vertex, path = queue.pop(0)
            for neighbor, _ in self.get_neighbors(vertex):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None


if __name__ == '__main__':
    g = Graph()
    g.add_edge('A', 'B')
    g.add_edge('A', 'C')
    g.add_edge('B', 'D')
    g.add_edge('C', 'D')
    print(f"DFS: {g.dfs('A')}")
    print(f"BFS: {g.bfs('A')}")
    print(f"Shortest path A->D: {g.shortest_path('A', 'D')}")
