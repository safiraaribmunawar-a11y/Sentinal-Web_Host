"""
Anomaly Detector
Combines rule-based scoring with Isolation Forest ML to detect threats.
Outputs a 0.0-1.0 threat score and a breakdown by category.
"""

import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from config import Config

log = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05,  # Expect ~5% anomalies
            n_estimators=100,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.baseline_stats = {}
        self._fitted = False

    # ------------------------------------------------------------------
    # Baseline Training
    # ------------------------------------------------------------------
    def fit_baseline(self, snapshots: list):
        """Train the ML model on baseline (clean) snapshots."""
        if len(snapshots) < 5:
            log.warning("Too few baseline snapshots for ML training. Using rules only.")
            return

        features = [self._extract_features(s) for s in snapshots]
        X = np.array(features)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self._fitted = True

        # Store baseline stats for rule-based scoring
        self.baseline_stats = {
            "cpu_mean": np.mean([s["cpu_percent"] for s in snapshots]),
            "cpu_std": max(np.std([s["cpu_percent"] for s in snapshots]), 1.0),
            "mem_mean": np.mean([s["mem_percent"] for s in snapshots]),
            "mem_std": max(np.std([s["mem_percent"] for s in snapshots]), 0.5),
            "net_recv_mean": np.mean([s["net_bytes_recv_rate"] for s in snapshots]),
            "net_recv_std": max(np.std([s["net_bytes_recv_rate"] for s in snapshots]), 1000),
            "net_sent_mean": np.mean([s["net_bytes_sent_rate"] for s in snapshots]),
            "net_sent_std": max(np.std([s["net_bytes_sent_rate"] for s in snapshots]), 1000),
        }
        log.info(
            f"ML baseline fitted on {len(snapshots)} samples. "
            f"Baseline CPU={self.baseline_stats['cpu_mean']:.1f}%, "
            f"MEM={self.baseline_stats['mem_mean']:.1f}%"
        )

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------
    def analyze(self, snapshot: dict) -> tuple[float, dict]:
        """
        Analyze a snapshot and return (threat_score, breakdown).
        threat_score: 0.0 (clean) to 1.0 (critical threat)
        breakdown: dict with individual component scores
        """
        cpu_score = self._score_cpu(snapshot)
        mem_score = self._score_memory(snapshot)
        net_score = self._score_network(snapshot)
        ml_score = self._score_ml(snapshot)

        # Weighted combination
        total = (
            cpu_score * Config.WEIGHT_CPU +
            mem_score * Config.WEIGHT_MEMORY +
            net_score * Config.WEIGHT_NETWORK +
            ml_score * Config.WEIGHT_ML
        )
        total = min(1.0, max(0.0, total))

        breakdown = {
            "cpu_score": round(cpu_score, 3),
            "memory_score": round(mem_score, 3),
            "network_score": round(net_score, 3),
            "ml_score": round(ml_score, 3),
            "total_score": round(total, 3),
            "indicators": self._get_indicators(snapshot, cpu_score, mem_score, net_score),
        }

        return total, breakdown

    # ------------------------------------------------------------------
    # Component Scorers
    # ------------------------------------------------------------------
    def _score_cpu(self, snap: dict) -> float:
        score = 0.0
        cpu = snap["cpu_percent"]
        max_core = snap.get("cpu_max_core", cpu)

        # Absolute threshold
        if cpu >= 95:
            score += 0.9
        elif cpu >= Config.CPU_ABS_THRESHOLD:
            score += 0.6
        elif cpu >= 70:
            score += 0.3

        # Deviation from baseline
        if self.baseline_stats:
            z = (cpu - self.baseline_stats["cpu_mean"]) / self.baseline_stats["cpu_std"]
            if z > 4:
                score += 0.5
            elif z > 3:
                score += 0.35
            elif z > 2:
                score += 0.2
            elif z > 1.5:
                score += 0.1

        # Single-core spike (often malware uses 1 core)
        if max_core >= 99:
            score += 0.3

        return min(1.0, score)

    def _score_memory(self, snap: dict) -> float:
        score = 0.0
        mem = snap["mem_percent"]
        swap = snap.get("swap_percent", 0)

        if mem >= Config.MEM_ABS_THRESHOLD:
            score += 0.6
        elif mem >= 75:
            score += 0.3

        if swap >= 80:
            score += 0.4
        elif swap >= 50:
            score += 0.2

        # Deviation from baseline
        if self.baseline_stats:
            z = (mem - self.baseline_stats["mem_mean"]) / self.baseline_stats["mem_std"]
            if z > 4:
                score += 0.5
            elif z > 3:
                score += 0.3
            elif z > 2:
                score += 0.15

        return min(1.0, score)

    def _score_network(self, snap: dict) -> float:
        score = 0.0
        recv = snap["net_bytes_recv_rate"]
        sent = snap["net_bytes_sent_rate"]
        errors = snap.get("net_errors", 0)
        MB = 1024 * 1024

        # Absolute thresholds
        if sent > Config.NET_ABS_THRESHOLD_MB * MB:
            score += 0.7   # Large outbound = data exfiltration risk
        elif sent > 10 * MB:
            score += 0.4

        if recv > Config.NET_ABS_THRESHOLD_MB * MB:
            score += 0.4
        elif recv > 20 * MB:
            score += 0.2

        # Deviation from baseline
        if self.baseline_stats:
            if self.baseline_stats["net_sent_mean"] > 0:
                ratio_sent = sent / self.baseline_stats["net_sent_mean"]
                if ratio_sent > Config.NET_SPIKE_MULTIPLIER * 2:
                    score += 0.5
                elif ratio_sent > Config.NET_SPIKE_MULTIPLIER:
                    score += 0.3

            if self.baseline_stats["net_recv_mean"] > 0:
                ratio_recv = recv / self.baseline_stats["net_recv_mean"]
                if ratio_recv > Config.NET_SPIKE_MULTIPLIER * 2:
                    score += 0.3
                elif ratio_recv > Config.NET_SPIKE_MULTIPLIER:
                    score += 0.15

        # Network errors can indicate scanning/attacks
        if errors > 100:
            score += 0.2
        elif errors > 20:
            score += 0.1

        return min(1.0, score)

    def _score_ml(self, snap: dict) -> float:
        """Use Isolation Forest to detect statistical anomaly."""
        if not self._fitted:
            return 0.0
        try:
            features = np.array([self._extract_features(snap)])
            features_scaled = self.scaler.transform(features)
            # decision_function: negative = anomaly, range roughly -0.5 to 0.5
            raw_score = self.model.decision_function(features_scaled)[0]
            # Convert: more negative = more anomalous → higher threat score
            # Normalize to 0-1: score of -0.5 → 1.0, score of 0.5 → 0.0
            normalized = max(0.0, min(1.0, (-raw_score + 0.5)))
            return normalized
        except Exception as e:
            log.debug(f"ML scoring error: {e}")
            return 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _extract_features(self, snap: dict) -> list:
        return [
            snap.get("cpu_percent", 0),
            snap.get("cpu_max_core", 0),
            snap.get("mem_percent", 0),
            snap.get("swap_percent", 0),
            min(snap.get("net_bytes_recv_rate", 0), 1e8),   # cap to prevent outlier domination
            min(snap.get("net_bytes_sent_rate", 0), 1e8),
            snap.get("net_packets_in_rate", 0),
            snap.get("net_packets_out_rate", 0),
            snap.get("net_errors", 0),
        ]

    def _get_indicators(self, snap, cpu_score, mem_score, net_score) -> list:
        """Return human-readable list of triggered indicators."""
        flags = []
        if cpu_score > 0.5:
            flags.append(f"CPU spike: {snap['cpu_percent']:.1f}%")
        if mem_score > 0.5:
            flags.append(f"Memory pressure: {snap['mem_percent']:.1f}%")
        if net_score > 0.5:
            sent_mb = snap['net_bytes_sent_rate'] / 1024 / 1024
            recv_mb = snap['net_bytes_recv_rate'] / 1024 / 1024
            flags.append(f"Network spike: ↑{sent_mb:.2f} MB/s ↓{recv_mb:.2f} MB/s")
        top = snap.get("top_processes", [])
        if top:
            top_name = top[0].get("name", "unknown")
            top_cpu = top[0].get("cpu_percent", 0)
            if top_cpu > 50:
                flags.append(f"High CPU process: {top_name} ({top_cpu:.1f}%)")
        return flags
