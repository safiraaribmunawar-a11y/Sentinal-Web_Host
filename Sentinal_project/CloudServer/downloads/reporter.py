"""
Threat Reporter
Sends threat reports and heartbeats to the Render dashboard backend.
Includes keep-alive loop and retry logic.
"""

import time
import logging
import threading
import requests
from datetime import datetime, timezone
from config import Config

log = logging.getLogger(__name__)


class ThreatReporter:
    def __init__(self, endpoint: str, device_id: str):
        self.device_id = device_id
        base = endpoint.strip()
        if "onrender.com" in base:
            parts = base.split("onrender.com")
            base = parts[0] + "onrender.com"
        self.base_url = base.rstrip("/")
        self._last_heartbeat      = 0
        self._last_severe_report  = 0
        self._severe_cooldown     = 1200  # 20 minutes

        log.info(f"Reporter base URL: {self.base_url}")

        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def send_report(self, metrics: dict, score: float, breakdown: dict, severity: str, note: str = ""):
        now = time.time()

        # 20-minute cooldown for SEVERE reports only
        if severity == "SEVERE":
            time_since_last = now - self._last_severe_report
            if time_since_last < self._severe_cooldown:
                remaining = int(self._severe_cooldown - time_since_last)
                log.info(f"SEVERE report suppressed (cooldown: {remaining}s remaining)")
                return
            self._last_severe_report = now

        if severity == "SEVERE":
            magnitude = int(200 + (score * 100))
        elif severity == "ELEVATED":
            magnitude = int(50 + (score * 150))
        else:
            magnitude = int(score * 50)

        payload = {
            "lat":          Config.DEVICE_LAT,
            "lon":          Config.DEVICE_LON,
            "magnitude":    magnitude,
            "device_id":    self.device_id,
            "severity":     severity,
            "threat_score": round(score, 4),
            "note":         note,
            "indicators":   breakdown.get("indicators", []),
        }
        self._post("/api/report", payload)

    def heartbeat(self, metrics: dict, severity: str):
        now = time.time()
        if now - self._last_heartbeat < Config.HEARTBEAT_INTERVAL:
            return
        self._last_heartbeat = now
        payload = {
            "device_id":   self.device_id,
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "type":        "heartbeat",
            "severity":    severity,
            "cpu_percent": metrics.get("cpu_percent"),
            "mem_percent": metrics.get("mem_percent"),
        }
        self._post("/api/heartbeat", payload)

    # ------------------------------------------------------------------
    # Keep-Alive — ping every 25s so Render never sleeps (sleeps at 50s)
    # ------------------------------------------------------------------
    def _keepalive_loop(self):
        while True:
            time.sleep(25)
            try:
                requests.get(self.base_url + "/", timeout=15)
                log.debug("Keep-alive ping sent")
            except Exception as e:
                log.debug(f"Keep-alive failed (ignored): {e}")

    # ------------------------------------------------------------------
    # HTTP POST with retry
    # ------------------------------------------------------------------
    def _post(self, path: str, payload: dict, retries: int = 3):
        url = self.base_url + path
        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    timeout=Config.REPORT_TIMEOUT,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    log.info(f"Report sent OK -> {url}")
                    return
                else:
                    log.warning(f"Report rejected: {resp.status_code} {resp.text[:100]}")
                    return
            except requests.exceptions.Timeout:
                log.warning(f"Timeout on attempt {attempt}/{retries} -> {url}")
                if attempt < retries:
                    time.sleep(5)
            except requests.exceptions.ConnectionError:
                log.warning(f"Cannot reach {url} — dropped.")
                return
            except Exception as e:
                log.error(f"Report error: {e}")
                return
        log.error(f"Report failed after {retries} attempts — dropped.")