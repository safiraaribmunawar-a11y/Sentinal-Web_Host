"""
System Monitor
Collects CPU, memory, and network metrics with rate calculation.
"""

import psutil
import time
import logging
from collections import deque
from config import Config

log = logging.getLogger(__name__)


class SystemMonitor:
    def __init__(self):
        self.history = deque(maxlen=Config.HISTORY_WINDOW)
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()

    def collect_snapshot(self) -> dict:
        """Collect a single point-in-time snapshot of system metrics."""
        now = time.time()

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        cpu_freq = psutil.cpu_freq()

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Network rates
        net_now = psutil.net_io_counters()
        dt = now - self._last_net_time
        if dt <= 0:
            dt = 1.0

        net_recv_rate = (net_now.bytes_recv - self._last_net.bytes_recv) / dt
        net_sent_rate = (net_now.bytes_sent - self._last_net.bytes_sent) / dt
        net_packets_in = (net_now.packets_recv - self._last_net.packets_recv) / dt
        net_packets_out = (net_now.packets_sent - self._last_net.packets_sent) / dt
        net_errors = net_now.errin + net_now.errout

        self._last_net = net_now
        self._last_net_time = now

        # Processes (top CPU consumers)
        top_procs = self._get_top_processes()

        snapshot = {
            "timestamp": now,
            "cpu_percent": cpu_percent,
            "cpu_per_core": cpu_per_core,
            "cpu_max_core": max(cpu_per_core) if cpu_per_core else cpu_percent,
            "cpu_freq_mhz": cpu_freq.current if cpu_freq else 0,
            "mem_percent": mem.percent,
            "mem_used_mb": mem.used / 1024 / 1024,
            "mem_available_mb": mem.available / 1024 / 1024,
            "mem_total_mb": mem.total / 1024 / 1024,
            "swap_percent": swap.percent,
            "net_bytes_recv_rate": max(0, net_recv_rate),
            "net_bytes_sent_rate": max(0, net_sent_rate),
            "net_packets_in_rate": max(0, net_packets_in),
            "net_packets_out_rate": max(0, net_packets_out),
            "net_errors": net_errors,
            "top_processes": top_procs,
        }

        self.history.append(snapshot)
        return snapshot

    def collect_baseline(self, duration: int) -> list:
        """Collect multiple snapshots over `duration` seconds for baseline."""
        snapshots = []
        start = time.time()
        while time.time() - start < duration:
            snap = self.collect_snapshot()
            snapshots.append(snap)
            log.info(
                f"Baseline [{len(snapshots)}]: CPU={snap['cpu_percent']:.1f}% "
                f"MEM={snap['mem_percent']:.1f}% "
                f"NET_IN={snap['net_bytes_recv_rate']:.0f}B/s"
            )
            time.sleep(2)
        return snapshots

    def get_memory_growth_rate(self) -> float:
        """
        Returns fractional memory growth over the history window.
        Positive = growing, negative = shrinking.
        """
        if len(self.history) < 2:
            return 0.0
        oldest = self.history[0]["mem_percent"]
        newest = self.history[-1]["mem_percent"]
        if oldest == 0:
            return 0.0
        return (newest - oldest) / oldest

    def get_history_averages(self) -> dict:
        """Return average values across the history window."""
        if not self.history:
            return {}
        keys = ["cpu_percent", "mem_percent", "net_bytes_recv_rate", "net_bytes_sent_rate"]
        return {
            k: sum(s[k] for s in self.history) / len(self.history)
            for k in keys
        }

    def _get_top_processes(self, n=5) -> list:
        """Return top N processes by CPU usage."""
        try:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:n]
        except Exception:
            return []