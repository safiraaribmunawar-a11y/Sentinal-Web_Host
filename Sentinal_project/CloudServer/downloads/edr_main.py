"""
EDR (Endpoint Detection & Response) - Main Entry Point
"""

import sys
import io
import logging

class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.buffer.write((msg + self.terminator).encode('utf-8', errors='replace'))
            stream.buffer.flush()
        except Exception:
            self.handleError(record)

import time
import threading
from collections import deque

from monitor import SystemMonitor
from detector import AnomalyDetector
from arduino_comm import ArduinoController
from reporter import ThreatReporter
from config import Config

file_handler = logging.FileHandler('edr.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))

stream_handler = UTF8StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])
log = logging.getLogger(__name__)


def main():
    log.info("=" * 60)
    log.info("  EDR System Starting Up")
    log.info(f"  Device ID: {Config.DEVICE_ID}")
    log.info(f"  Report endpoint: {Config.REPORT_URL}")
    log.info("=" * 60)

    monitor  = SystemMonitor()
    detector = AnomalyDetector()
    arduino  = ArduinoController(port=Config.ARDUINO_PORT, baudrate=Config.ARDUINO_BAUD)
    reporter = ThreatReporter(endpoint=Config.REPORT_URL, device_id=Config.DEVICE_ID)

    arduino.connect()

    log.info(f"Collecting baseline for {Config.BASELINE_DURATION} seconds...")
    baseline_data = monitor.collect_baseline(duration=Config.BASELINE_DURATION)
    detector.fit_baseline(baseline_data)
    log.info("Baseline established. EDR is now active.")

    current_severity = "SECURE"
    severe_cooldown  = 0
    score_history    = deque(maxlen=Config.SMOOTHING_WINDOW)
    handling_severe  = False

    try:
        while True:
            metrics = monitor.collect_snapshot()
            raw_score, breakdown = detector.analyze(metrics)

            score_history.append(raw_score)
            smoothed_score = sum(score_history) / len(score_history)
            new_severity   = _score_to_severity(smoothed_score)

            log.info(
                f"Score: {smoothed_score:.2f} (raw: {raw_score:.2f}) | "
                f"Severity: {new_severity} | "
                f"CPU: {metrics['cpu_percent']:.1f}% | "
                f"MEM: {metrics['mem_percent']:.1f}% | "
                f"NET_IN: {metrics['net_bytes_recv_rate']:.0f} B/s | "
                f"NET_OUT: {metrics['net_bytes_sent_rate']:.0f} B/s"
            )

            # Skip severity changes while handling a severe alert
            if handling_severe:
                reporter.heartbeat(metrics, current_severity)
                time.sleep(Config.POLL_INTERVAL)
                continue

            if new_severity != current_severity:
                log.warning(f"Severity changed: {current_severity} -> {new_severity}")
                current_severity = new_severity

                # Only send report immediately for non-SEVERE changes
                if new_severity != "SEVERE":
                    reporter.send_report(metrics, smoothed_score, breakdown, current_severity)

                if new_severity == "SEVERE" and severe_cooldown <= 0:
                    severe_cooldown = Config.SEVERE_COOLDOWN
                    handling_severe = True
                    score_history.clear()

                    arduino.set_led("YELLOW")
                    arduino._send("WARN:20")

                    # BLOCKING — main loop pauses here until code entered or timeout
                    code_accepted = _prompt_security_code(
                        countdown=20,
                        security_code=Config.SECURITY_CODE,
                        arduino=arduino
                    )

                    handling_severe = False

                    if code_accepted:
                        log.info("Code accepted. Returning to ELEVATED.")
                        current_severity = "ELEVATED"
                        arduino.set_led("YELLOW")
                        reporter.send_report(metrics, smoothed_score, breakdown, "ELEVATED", note="Code accepted")
                    else:
                        log.error("Code failed. RED alert.")
                        current_severity = "SEVERE"
                        arduino.set_led("RED")
                        # Report only sent AFTER timeout — not before
                        reporter.send_report(metrics, smoothed_score, breakdown, "SEVERE", note="Code timeout")

                        # Lock in RED until kill switch
                        log.warning("System locked RED. Flip kill switch to reset.")
                        print("\n" + "=" * 52)
                        print("  SYSTEM LOCKED - RED ALERT ACTIVE")
                        print("  Flip the kill switch to reset.")
                        print("=" * 52 + "\n")

                        while not arduino.kill_switch_active():
                            metrics = monitor.collect_snapshot()
                            reporter.heartbeat(metrics, "SEVERE")
                            time.sleep(Config.POLL_INTERVAL)

                        log.warning("KILL SWITCH ACTIVATED - Resetting to SECURE")
                        current_severity = "SECURE"
                        severe_cooldown  = 0
                        score_history.clear()
                        arduino.set_led("GREEN")
                        reporter.send_report(metrics, 0.0, {}, "SECURE", note="Kill switch activated")

                elif new_severity == "ELEVATED":
                    arduino.set_led("YELLOW")

                elif new_severity == "SECURE":
                    arduino.set_led("GREEN")
                    severe_cooldown = 0
                    score_history.clear()

            if severe_cooldown > 0:
                severe_cooldown -= Config.POLL_INTERVAL

            reporter.heartbeat(metrics, current_severity)
            time.sleep(Config.POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("EDR shutting down.")
        arduino.set_led("GREEN")
        arduino.disconnect()


def _prompt_security_code(countdown: int, security_code: str, arduino) -> bool:
    """
    Fully blocking code entry with live countdown.
    Returns True if correct code entered in time, False otherwise.
    """
    # Arduino keypad mode — only if keypad is actually sending codes
    if arduino._connected and arduino._last_code is not None:
        arduino._last_code = None
        deadline = time.time() + countdown
        log.warning(f"Waiting for keypad code ({countdown}s)...")
        while time.time() < deadline:
            if arduino._last_code == security_code:
                arduino._last_code = None
                arduino._send("CANCEL")
                return True
            time.sleep(0.5)
        return False

    # Terminal mode — flush buffered keystrokes
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except Exception:
        pass

    deadline = time.time() + countdown
    entered  = ""

    print("\n" + "=" * 52)
    print("  !! SEVERE ALERT - ENTER SECURITY CODE !!")
    print(f"  You have {countdown} seconds. Type code + Enter.")
    print("=" * 52)

    try:
        import msvcrt
        while True:
            remaining = int(deadline - time.time())
            if remaining <= 0:
                print(f"\r  [{countdown - remaining:2d}s] Code: {entered}  ")
                print("\n\n  [!!] Timeout! RED alert triggered.\n")
                return False

            sys.stdout.write(f"\r  [{remaining:2d}s] Code: {entered}   ")
            sys.stdout.flush()

            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\r', '\n'):
                    print("")
                    break
                elif ch == '\b':
                    entered = entered[:-1]
                elif ch.isprintable():
                    entered += ch

            time.sleep(0.05)

    except Exception:
        entered = input(f"\n  Code: ").strip()

    print("")
    if entered == security_code:
        print("  [OK] Correct code! Alert cancelled.\n")
        return True
    else:
        print("  [!!] Wrong code. RED alert triggered.\n")
        return False


def _score_to_severity(score: float) -> str:
    if score >= Config.THRESHOLD_SEVERE:
        return "SEVERE"
    elif score >= Config.THRESHOLD_ELEVATED:
        return "ELEVATED"
    return "SECURE"


if __name__ == "__main__":
    main()
