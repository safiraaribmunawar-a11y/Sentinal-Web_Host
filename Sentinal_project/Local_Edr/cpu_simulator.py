import multiprocessing
import time
import math
import random

print("CPU Burst Simulator")
print("Press CTRL+C to stop")

def cpu_burst():
    while True:
        end_time = time.time() + random.uniform(1.0, 2.5)
        while time.time() < end_time:
            math.sqrt(12345.6789)

        time.sleep(random.uniform(1.0, 3.0))

if __name__ == "__main__":
    processes = []
    cores = multiprocessing.cpu_count()

    for _ in range(max(1, cores // 2)):
        p = multiprocessing.Process(target=cpu_burst)
        p.start()
        processes.append(p)

