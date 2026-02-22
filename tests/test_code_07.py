"""Tests for genCodes.code_07 (Stack, Queue)."""
import pytest
from genCodes import code_07


def test_stack_push_pop_peek():
    stack = code_07.Stack()
    assert stack.is_empty()
    stack.push(1)
    stack.push(2)
    assert stack.size() == 2
    assert stack.peek() == 2
    assert stack.pop() == 2
    assert stack.pop() == 1
    assert stack.pop() is None
    assert stack.is_empty()


def test_queue_enqueue_dequeue():
    queue = code_07.Queue()
    assert queue.is_empty()
    queue.enqueue("a")
    queue.enqueue("b")
    assert queue.size() == 2
    assert queue.front() == "a"
    assert queue.dequeue() == "a"
    assert queue.dequeue() == "b"
    assert queue.dequeue() is None
