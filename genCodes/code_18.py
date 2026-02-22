
import threading
import time
from queue import PriorityQueue, Empty

class Task:
    """Represents a task to be executed."""

    def __init__(self, task_id, priority, func, *args, **kwargs):
        self.task_id = task_id
        self.priority = priority
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.completed = False
        self.error = None

    def __lt__(self, other):
        """Compare tasks by priority (higher priority first)."""
        return self.priority > other.priority

    def execute(self):
        """Execute the task."""
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.completed = True
        except Exception as e:
            self.error = str(e)
            self.completed = True

    def __repr__(self):
        status = 'completed' if self.completed else 'pending'
        return f'Task({self.task_id}, priority={self.priority}, status={status})'


class TaskScheduler:
    """Manages and executes tasks with priority."""

    def __init__(self, num_workers=2):
        self.num_workers = num_workers
        self.task_queue = PriorityQueue()
        self.workers = []
        self.running = False
        self.lock = threading.Lock()
        self.completed_tasks = []

    def add_task(self, task):
        """Add a task to the queue."""
        self.task_queue.put(task)

    def _worker(self):
        """Worker thread that processes tasks."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    continue  # Signal to exit worker
                task.execute()
                with self.lock:
                    self.completed_tasks.append(task)
                self.task_queue.task_done()
            except Exception as e:
                print(f'Worker error: {e}')

    def start(self):
        """Start the scheduler."""
        if self.running:
            return

        self.running = True
        self.workers = []
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        for _ in range(self.num_workers):
            self.task_queue.put(None)  # Signal workers to exit
        for worker in self.workers:
            worker.join()

    def wait_for_completion(self):
        """Wait for all tasks to complete."""
        self.task_queue.join()

    def get_results(self):
        """Get results of completed tasks."""
        return [(task.task_id, task.result, task.error) for task in self.completed_tasks]


def sample_task(task_id, duration):
    """Sample task function."""
    time.sleep(duration)
    return f'Task {task_id} completed'

if __name__ == '__main__':
    scheduler = TaskScheduler(num_workers=2)
    scheduler.start()

    for i in range(5):
        task = Task(i, priority=i % 3, func=sample_task, task_id=i, duration=0.1)
        scheduler.add_task(task)

    scheduler.wait_for_completion()
    scheduler.stop()
    results = scheduler.get_results()

    for task_id, result, error in results:
        if error:
            print(f'Task {task_id} failed: {error}')
        else:
            print(f'Task {task_id}: {result}')
