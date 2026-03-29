"""
EDR Stress Test Suite
Run this in a SEPARATE terminal while EDR is running.
Press Ctrl+C to stop any test.
"""

import threading
import multiprocessing
import time
import os
import sys


# ── 1. CPU STRESS (uses multiprocessing to bypass Python GIL) ─────────────────
def _cpu_worker():
    """Runs in a real separate process — true CPU saturation."""
    while True:
        x = 0
        for i in range(10**8):
            x += i * i * i


def stress_cpu():
    core_count = os.cpu_count() or 4
    print(f"[CPU STRESS] Launching {core_count} real processes (bypasses GIL)...")
    print("[CPU STRESS] This will max out all cores. Press Ctrl+C to stop.")

    processes = [multiprocessing.Process(target=_cpu_worker, daemon=True) for _ in range(core_count)]
    for p in processes:
        p.start()

    try:
        while True:
            alive = sum(p.is_alive() for p in processes)
            print(f"[CPU STRESS] {alive}/{core_count} worker processes running")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[CPU STRESS] Stopping all processes...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()


# ── 2. MEMORY STRESS ──────────────────────────────────────────────────────────
def stress_memory():
    print("[MEMORY STRESS] Rapidly allocating memory... Press Ctrl+C to stop.")
    chunks = []
    chunk_mb = 100

    try:
        while True:
            chunk = bytearray(chunk_mb * 1024 * 1024)
            for i in range(0, len(chunk), 4096):
                chunk[i] = 1
            chunks.append(chunk)
            total_mb = len(chunks) * chunk_mb
            print(f"[MEMORY STRESS] Allocated {total_mb} MB ({total_mb/1024:.2f} GB) total")
            time.sleep(1)
    except MemoryError:
        print("[MEMORY STRESS] System out of memory!")
    except KeyboardInterrupt:
        print(f"\n[MEMORY STRESS] Stopping... Freeing {len(chunks) * chunk_mb} MB")
        chunks.clear()


# ── 3. NETWORK STRESS ─────────────────────────────────────────────────────────
def stress_network():
    print("[NETWORK STRESS] Flooding outbound connections... Press Ctrl+C to stop.")
    import urllib.request
    import socket

    download_urls = [
        "http://speedtest.tele2.net/10MB.zip",
        "http://proof.ovh.net/files/10Mb.dat",
        "http://ipv4.download.thinkbroadband.com/10MB.zip",
    ]

    count = 0
    bytes_total = 0
    stop_event = threading.Event()

    def download_loop():
        nonlocal count, bytes_total
        while not stop_event.is_set():
            for url in download_urls:
                if stop_event.is_set():
                    break
                try:
                    req = urllib.request.urlopen(url, timeout=5)
                    data = req.read(5 * 1024 * 1024)
                    bytes_total += len(data)
                    count += 1
                except Exception:
                    pass

    def connect_flood():
        hosts = ["8.8.8.8", "1.1.1.1", "8.8.4.4", "9.9.9.9"]
        while not stop_event.is_set():
            for host in hosts:
                if stop_event.is_set():
                    break
                try:
                    s = socket.create_connection((host, 80), timeout=1)
                    s.send(b"GET / HTTP/1.0\r\n\r\n")
                    s.recv(1024)
                    s.close()
                except Exception:
                    pass

    threads = [threading.Thread(target=download_loop, daemon=True) for _ in range(4)]
    threads.append(threading.Thread(target=connect_flood, daemon=True))
    for t in threads:
        t.start()

    try:
        while True:
            print(f"[NETWORK STRESS] {count} requests | {bytes_total/1024/1024:.1f} MB transferred")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[NETWORK STRESS] Stopping...")
        stop_event.set()


# ── 4. COMBINED ────────────────────────────────────────────────────────────────
def stress_combined():
    print("[COMBINED] CPU + Memory + Network. Most likely to trigger SEVERE.")
    print("[COMBINED] Press Ctrl+C to stop.")

    stop_event = threading.Event()
    chunks = []

    # Real CPU processes
    core_count = os.cpu_count() or 4
    processes = [multiprocessing.Process(target=_cpu_worker, daemon=True) for _ in range(core_count)]
    for p in processes:
        p.start()
    print(f"[COMBINED] {core_count} CPU processes running")

    # Memory thread
    def eat_memory():
        while not stop_event.is_set():
            try:
                chunk = bytearray(50 * 1024 * 1024)
                for i in range(0, len(chunk), 4096):
                    chunk[i] = 1
                chunks.append(chunk)
                print(f"[COMBINED] Memory: {len(chunks) * 50} MB allocated")
                time.sleep(3)
            except MemoryError:
                print("[COMBINED] Memory full, holding...")
                time.sleep(5)

    threading.Thread(target=eat_memory, daemon=True).start()

    # Network thread
    import urllib.request
    def net_flood():
        while not stop_event.is_set():
            try:
                urllib.request.urlopen(
                    "http://speedtest.tele2.net/10MB.zip", timeout=5
                ).read(2 * 1024 * 1024)
            except Exception:
                pass

    for _ in range(3):
        threading.Thread(target=net_flood, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[COMBINED] Stopping all stress tests...")
        stop_event.set()
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        chunks.clear()


# ── MENU ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  EDR STRESS TEST SUITE")
    print("=" * 50)
    print("  1. CPU Stress      (real multiprocessing)")
    print("  2. Memory Stress   (rapid allocation)")
    print("  3. Network Stress  (download flood)")
    print("  4. Combined        (all three at once)")
    print("=" * 50)
    choice = input("Select test [1-4]: ").strip()

    if choice == "1":
        stress_cpu()
    elif choice == "2":
        stress_memory()
    elif choice == "3":
        stress_network()
    elif choice == "4":
        stress_combined()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # needed for Windows
    main()