"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: benchmark.py
Description: High-resolution timing metrics utility tracking STT latency, TTFT, and TTFA telemetry.
"""

import time


class Benchmark:
    _timestamps: dict = {}
    last_stt_ms: float = 0.0
    last_ttft_ms: float = 0.0
    last_ttfa_ms: float = 0.0

    @classmethod
    def start(cls, key: str):
        """Record the start time for a given performance metric."""
        cls._timestamps[key] = time.perf_counter()

    @classmethod
    def get_start_time(cls, key: str):
        """Retrieve start timestamp for relative measurements."""
        return cls._timestamps.get(key)

    @classmethod
    def record_start(cls, key: str, timestamp: float):
        """Explicitly set the start timestamp."""
        cls._timestamps[key] = timestamp

    @classmethod
    def end(cls, key: str) -> float:
        """Record the end time, remove key, and return duration in milliseconds."""
        if key in cls._timestamps:
            duration = (time.perf_counter() - cls._timestamps.pop(key)) * 1000
            return duration
        return 0.0

    @classmethod
    def log_metrics(cls, stt_ms: float, ttft_ms: float, ttfa_ms: float):
        """Prints latency metrics to console telemetry."""
        print(f"[Benchmark] Telemetry -> STT: {stt_ms:.1f}ms, TTFT: {ttft_ms:.1f}ms, TTFA: {ttfa_ms:.1f}ms", flush=True)

