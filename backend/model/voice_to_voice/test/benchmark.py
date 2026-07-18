import time
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "benchmark_log.csv")

class Benchmark:
    _timestamps = {}

    @classmethod
    def start(cls, key):
        """Record the start time for a given performance metric."""
        cls._timestamps[key] = time.perf_counter()

    @classmethod
    def get_start_time(cls, key):
        """Retrieve start timestamp for relative measurements."""
        return cls._timestamps.get(key)

    @classmethod
    def record_start(cls, key, timestamp):
        """Explicitly set the start timestamp."""
        cls._timestamps[key] = timestamp

    @classmethod
    def end(cls, key):
        """Record the end time and return the duration in milliseconds."""
        if key in cls._timestamps:
            duration = (time.perf_counter() - cls._timestamps[key]) * 1000
            # Keep it in storage in case we need it for compound metrics, but clean up is standard
            return duration
        return 0.0

    @classmethod
    def log_metrics(cls, stt_ms, ttft_ms, ttfa_ms):
        """Appends metrics to a local CSV file."""
        file_exists = os.path.exists(CSV_PATH)
        try:
            with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "stt_ms", "ttft_ms", "ttfa_ms"])
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{stt_ms:.2f}",
                    f"{ttft_ms:.2f}",
                    f"{ttfa_ms:.2f}"
                ])
            print(f"[Benchmark] Logged -> STT: {stt_ms:.1f}ms, TTFT: {ttft_ms:.1f}ms, TTFA: {ttfa_ms:.1f}ms")
        except Exception as e:
            print(f"[Benchmark Error] Failed to write CSV: {e}")
