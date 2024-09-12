import time
from typing import Callable, List, Tuple, Any
from FlashSQL import Client
from tabulate import tabulate

QUERY_COUNT = 100000  # Number of queries to benchmark
KEY_LENGTH = 10       # Length of the key
VALUE_LENGTH = 50     # Length of the value

class BenchmarkResult:
    def __init__(self, operation: str, total_time: float, avg_latency: float, ops_per_second: float) -> None:
        self.operation = operation
        self.total_time = total_time
        self.avg_latency = avg_latency
        self.ops_per_second = ops_per_second

class Benchmark:
    def __init__(self, db: Client) -> None:
        self.db = db

    def random_string(self, length: int) -> str:
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase, k=length))

    def format_time(self, seconds: float) -> str:
        return f"{seconds:.2f}"

    def run(self, name: str, action: Callable[[Client, Any], None], data: Any) -> BenchmarkResult:
        print(f"\n* Running Benchmark: {name}")

        start = time.time()
        action(self.db, data)
        duration = time.time() - start

        average_latency = (duration * 1000) / QUERY_COUNT
        operations_per_second = QUERY_COUNT / duration

        print(f"* Benchmark Complete: {name}")
        return BenchmarkResult(name, duration, average_latency, operations_per_second)

    def prepare_data(self) -> Tuple[List[str], List[str], List[Tuple[str, str]]]:
        keys = [self.random_string(KEY_LENGTH) for _ in range(QUERY_COUNT)]
        values = [self.random_string(VALUE_LENGTH) for _ in range(QUERY_COUNT)]
        key_value_pairs = list(zip(keys, values))
        return keys, values, key_value_pairs

    def execute_benchmarks(self) -> None:
        keys, values, key_value_pairs = self.prepare_data()

        benchmarks = [
            ("Set", lambda db, data: [db.set(key, value) for key, value in data], key_value_pairs),
            ("Set Many", lambda db, data: db.set_many({key: (value, None) for key, value in data}), key_value_pairs),
            ("Exists", lambda db, data: [db.exists(key) for key in data], keys),
            ("Get Expire", lambda db, data: [db.get_expire(key) for key in data], keys),
            ("Set Expire", lambda db, data: [db.set_expire(key, 31536000) for key in data], keys),
            ("Get", lambda db, data: [db.get(key) for key in data], keys),
            ("Get Many", lambda db, data: db.get_many(data), keys),
            ("Delete", lambda db, data: [db.delete(key) for key in data], keys),
            ("Delete Many", lambda db, data: db.delete_many(data), keys),
        ]

        results = [self.run(name, action, data) for name, action, data in benchmarks]
        self.display_results(results)

        self.db.cleanup()
        self.db.close()
        print("\nBenchmark completed.")

    def display_results(self, results: List[BenchmarkResult]) -> None:
        table = []
        for result in results:
            table.append([
                result.operation,
                self.format_time(result.total_time),
                f"{result.avg_latency:.2f}",
                f"{result.ops_per_second:.2f}"
            ])

        headers = ["Operation", "Total Time (s)", "Average Latency (ms)", "Ops/Second"]
        print("\nBenchmark Results:")
        print(tabulate(table, headers=headers, tablefmt="grid"))

db = Client(":memory:")  
benchmark = Benchmark(db)
benchmark.execute_benchmarks()
