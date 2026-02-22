
import time

class SortingAlgorithms:
    @staticmethod
    def bubble_sort(arr):
        """Bubble sort algorithm."""
        arr = arr.copy()
        n = len(arr)
        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
            if not swapped:
                break
        return arr

    @staticmethod
    def quick_sort(arr):
        """Quick sort algorithm."""
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return SortingAlgorithms.quick_sort(left) + middle + SortingAlgorithms.quick_sort(right)

    @staticmethod
    def merge_sort(arr):
        """Merge sort algorithm."""
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = SortingAlgorithms.merge_sort(arr[:mid])
        right = SortingAlgorithms.merge_sort(arr[mid:])
        return SortingAlgorithms._merge(left, right)

    @staticmethod
    def _merge(left, right):
        """Merge two sorted arrays."""
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    @staticmethod
    def insertion_sort(arr):
        """Insertion sort algorithm."""
        arr = arr.copy()
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr

class SortPerformanceTracker:
    """Tracks performance of sorting algorithms."""
    def __init__(self):
        self.results = {}

    def benchmark(self, algorithm_name, algorithm_func, test_data):
        """Benchmark a sorting algorithm."""
        import time
        start_time = time.perf_counter()
        sorted_data = algorithm_func(test_data)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        is_sorted = self._verify_sorted(sorted_data)
        self.results[algorithm_name] = {'time': execution_time, 'sorted': is_sorted, 'data_length': len(test_data)}
        return sorted_data

    def _verify_sorted(self, arr):
        """Verify if array is sorted."""
        return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))

if __name__ == '__main__':
    test_data = [64, 34, 25, 12, 22, 11, 90, 5]
    tracker = SortPerformanceTracker()
    tracker.benchmark('Bubble Sort', SortingAlgorithms.bubble_sort, test_data)
    tracker.benchmark('Quick Sort', SortingAlgorithms.quick_sort, test_data)
    tracker.benchmark('Merge Sort', SortingAlgorithms.merge_sort, test_data)
    tracker.benchmark('Insertion Sort', SortingAlgorithms.insertion_sort, test_data)

    for algo, result in tracker.results.items():
        print(f"{algo}: {result['time'] * 1000:.4f}ms, Sorted: {result['sorted']}")
