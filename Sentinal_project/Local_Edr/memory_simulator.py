import time

print("Memory Growth Simulator Running")
print("Press CTRL+C to stop")

data = []

try:
    while True:
        data.append("X" * 5_000_000)
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMemory simulator stopped")
