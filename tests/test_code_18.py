"""Tests for genCodes.code_18 (Task, TaskScheduler)."""
import pytest
from genCodes import code_18


def test_task_execute():
    result_holder = []

    def simple_func(x, y):
        return x + y

    task = code_18.Task("t1", 1, simple_func, 2, 3)
    assert not task.completed
    task.execute()
    assert task.completed
    assert task.result == 5
    assert task.error is None


def test_task_scheduler_add_and_run():
    results = []

    def quick_task(val):
        results.append(val)
        return val * 2

    scheduler = code_18.TaskScheduler(num_workers=1)
    scheduler.start()
    for i in range(3):
        task = code_18.Task(f"task_{i}", 0, quick_task, i)
        scheduler.add_task(task)
    scheduler.wait_for_completion()
    scheduler.stop()
    assert len(scheduler.completed_tasks) == 3
    ids_and_results = [(t.task_id, t.result) for t in scheduler.completed_tasks]
    assert len(ids_and_results) == 3
