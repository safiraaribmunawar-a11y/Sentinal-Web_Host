"""
Arduino Controller
Handles serial communication with the Arduino hardware.
Includes terminal fallback when Arduino is not connected.
"""

import threading
import time
import logging

log = logging.getLogger(__name__)

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    log.warning("pyserial not installed. Arduino communication disabled.")


class ArduinoController:
    def __init__(self, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._connected = False
        self._kill_switch = False
        self._last_code = None
        self._reader_thread = None
        self._running = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    def connect(self) -> bool:
        if not SERIAL_AVAILABLE:
            log.warning("Arduino: pyserial unavailable, running in terminal mode.")
            return False
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            self._connected = True
            self._running = True
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            log.info(f"Arduino connected on {self.port} @ {self.baudrate} baud")
            self.set_led("GREEN")
            return True
        except Exception as e:
            log.warning(f"Arduino connection failed ({e}). Running in terminal mode.")
            return False

    def disconnect(self):
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._connected = False

    # ------------------------------------------------------------------
    # LED Control
    # ------------------------------------------------------------------
    def set_led(self, color: str):
        color = color.upper()
        assert color in ("GREEN", "YELLOW", "RED"), f"Invalid color: {color}"
        self._send(f"LED:{color}")
        log.info(f"Arduino LED -> {color}")

    # ------------------------------------------------------------------
    # Severe Warning
    # ------------------------------------------------------------------
    def trigger_severe_warning(self, countdown: int, on_timeout, security_code: str, on_complete=None):
        """
        Starts the 20s warning countdown.
        on_timeout  : called if code not entered in time
        on_complete : called when code is correctly entered
        """
        self._send(f"WARN:{countdown}")
        log.warning(f"!! SEVERE WARNING - {countdown}s to enter security code!")

        if self._connected:
            # Arduino connected — wait for keypad input
            def keypad_thread():
                deadline = time.time() + countdown
                while time.time() < deadline:
                    if self._last_code == security_code:
                        log.info("CORRECT CODE - Severe alert cancelled.")
                        self._send("CANCEL")
                        self._last_code = None
                        if on_complete:
                            on_complete()
                        return
                    time.sleep(0.5)
                log.error("XX Security code timeout! Triggering RED alert.")
                on_timeout()

            threading.Thread(target=keypad_thread, daemon=True).start()
        else:
            # No Arduino — prompt in terminal
            self._terminal_input(countdown, security_code, on_timeout, on_complete)

    def _terminal_input(self, countdown: int, security_code: str, on_timeout, on_complete):
        """Blocks terminal input for up to countdown seconds."""
        def input_thread():
            print("\n" + "=" * 52)
            print(f"  !! SEVERE ALERT !!")
            print(f"  You have {countdown} seconds to enter the security code.")
            print(f"  Type your code and press Enter:")
            print("=" * 52)

            entered = [None]
            input_ready = threading.Event()

            def read():
                try:
                    entered[0] = input("  Code: ").strip()
                except Exception:
                    pass
                input_ready.set()

            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            input_ready.wait(timeout=countdown)

            print("")  # newline after input

            if entered[0] == security_code:
                log.info("CORRECT CODE - Severe alert cancelled.")
                print("  [OK] Correct code! Alert cancelled.\n")
                if on_complete:
                    on_complete()
            elif entered[0] is None:
                log.error("XX Timeout! No code entered. Triggering RED alert.")
                print("  [!!] Timeout! RED alert triggered.\n")
                on_timeout()
            else:
                log.error(f"XX Wrong code: '{entered[0]}'. Triggering RED alert.")
                print("  [!!] Wrong code! RED alert triggered.\n")
                on_timeout()

        threading.Thread(target=input_thread, daemon=True).start()

    # ------------------------------------------------------------------
    # Kill Switch
    # ------------------------------------------------------------------
    def kill_switch_active(self) -> bool:
        if self._kill_switch:
            self._kill_switch = False
            return True
        return False

    # ------------------------------------------------------------------
    # Serial I/O
    # ------------------------------------------------------------------
    def _send(self, message: str):
        if not self._connected or not SERIAL_AVAILABLE:
            log.debug(f"[SIMULATED] Arduino <- {message}")
            return
        try:
            self._serial.write(f"{message}\n".encode("utf-8"))
        except Exception as e:
            log.error(f"Arduino send error: {e}")

    def _read_loop(self):
        while self._running:
            try:
                if self._serial and self._serial.in_waiting:
                    line = self._serial.readline().decode("utf-8").strip()
                    if line:
                        self._handle_message(line)
            except Exception as e:
                log.debug(f"Arduino read error: {e}")
            time.sleep(0.1)

    def _handle_message(self, message: str):
        log.debug(f"Arduino -> PC: {message}")
        if message.startswith("KILL:"):
            state = message.split(":")[1]
            self._kill_switch = (state == "1")
            log.info(f"Kill switch {'ACTIVATED' if self._kill_switch else 'deactivated'}")
        elif message.startswith("CODE:"):
            code = message.split(":")[1]
            log.info(f"Security code received from keypad: {code}")
            self._last_code = code
        else:
            log.debug(f"Unknown Arduino message: {message}")