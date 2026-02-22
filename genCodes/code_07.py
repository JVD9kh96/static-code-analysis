
class Stack:
    """A stack data structure (LIFO)."""

    def __init__(self):
        """Initialize an empty stack."""
        self.items = []

    def push(self, item):
        """Push an item onto the stack."""
        self.items.append(item)

    def pop(self):
        """Pop an item from the stack."""
        if self.is_empty():
            return None  # Or raise an exception
        return self.items.pop()

    def peek(self):
        """Peek at the top item without removing it."""
        if self.is_empty():
            return None  # Or raise an exception
        return self.items[-1]

    def is_empty(self):
        """Check if stack is empty."""
        return len(self.items) == 0

    def size(self):
        """Get the size of the stack."""
        return len(self.items)


class Queue:
    """A queue data structure (FIFO)."""

    def __init__(self):
        """Initialize an empty queue."""
        self.items = []

    def enqueue(self, item):
        """Add an item to the queue."""
        self.items.append(item)

    def dequeue(self):
        """Remove and return the first item."""
        if self.is_empty():
            return None  # Or raise an exception
        return self.items.pop(0)

    def front(self):
        """Get the front item without removing it."""
        if self.is_empty():
            return None  # Or raise an exception
        return self.items[0]

    def is_empty(self):
        """Check if queue is empty."""
        return len(self.items) == 0

    def size(self):
        """Get the size of the queue."""
        return len(self.items)


if __name__ == '__main__':
    stack = Stack()
    stack.push(1)
    stack.push(2)
    stack.push(3)
    print(f'Stack size: {stack.size()}')
    print(f'Popped: {stack.pop()}')

    queue = Queue()
    queue.enqueue(1)
    queue.enqueue(2)
    queue.enqueue(3)
    print(f'Queue size: {queue.size()}')
    print(f'Dequeued: {queue.dequeue()}')
