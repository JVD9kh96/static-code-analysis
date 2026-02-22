
class LRUCache:
    """LRU Cache implementation."""

    def __init__(self, capacity):
        """Initialize the LRU cache with a given capacity."""
        if capacity <= 0:
            self.capacity = 0
            self.cache = {}
            self.access_order = []
        else:
            self.capacity = capacity
            self.cache = {}
            self.access_order = []

    def get(self, key):
        """Get value by key and update access order."""
        if key in self.cache:
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        else:
            return None

    def put(self, key, value):
        """Put key-value pair and handle eviction if needed."""
        if key in self.cache:
            self.cache[key] = value
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            if len(self.cache) >= self.capacity:
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]  # Remove the least recently used key from the cache

            self.cache[key] = value
            self.access_order.append(key)

    def remove(self, key):
        """Remove a key from cache."""
        if key in self.cache:
            self.access_order.remove(key)
            del self.cache[key]  # Remove the key from the cache

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()

    def size(self):
        """Get current cache size."""
        return len(self.cache)

    def is_full(self):
        """Check if cache is full."""
        return len(self.cache) >= self.capacity


if __name__ == '__main__':
    cache = LRUCache(3)
    cache.put('a', 1)
    cache.put('b', 2)
    cache.put('c', 3)
    print(f"Get 'a': {cache.get('a')}")
    cache.put('d', 4)
    print(f"Get 'b': {cache.get('b')}")
    print(f'Cache size: {cache.size()}')
