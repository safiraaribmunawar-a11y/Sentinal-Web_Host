import psutil, time, serial, requests, os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# --- CONFIG ---
CLOUD_URL = "https://sentinel-mesh.onrender.com/api/report"
COM_PORT = 'COM3' 
BAUD_RATE = 9600
SECURITY_KEY = "admin123"
LAT, LON = 23.8103, 90.4125

# --- SETUP ---
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2)
    print(f"✅ Hardware Connected on {COM_PORT}")
except:
    print("⚠️ Hardware not found. Continuing in software mode.")
    ser = None

scaler = StandardScaler()
model = IsolationForest(contamination=0.05, random_state=42)

def get_metrics():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    n1 = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    time.sleep(0.5)
    n2 = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    return [cpu, ram, (n2 - n1)]

def sync_cloud(status, mag):
    try:
        requests.post(CLOUD_URL, json={"lat": LAT, "lon": LON, "magnitude": mag}, timeout=2)
    except: pass

# --- BASELINE ---
print("[!] SentinelCore: Learning System Baseline (20s)...")
train = [get_metrics() for _ in range(20)]
scaler.fit(train)
model.fit(scaler.transform(train))
print("✅ Baseline Locked.\n")

# --- LOOP ---
try:
    while True:
        m = get_metrics()
        pred = model.predict(scaler.transform([m]))[0]
        cpu, ram, _ = m
        
        score = sum([cpu > 85, ram > 85, pred == -1])
        status = "SAFE"; mag = 25
        if cpu > 98 or score >= 2: status = "SEVERE"; mag = 350
        elif score == 1: status = "ELEVATED"; mag = 150

        print(f"📊 CPU: {cpu}% | STATUS: {status}")
        if ser: ser.write(f"{status}\n".encode())
        sync_cloud(status, mag)

        if status == "SEVERE":
            start = time.time()
            while time.time() - start < 20:
                key = input("🚨 ENTER SECURITY KEY: ")
                if key == SECURITY_KEY: break
        time.sleep(1)
except KeyboardInterrupt:
    if ser: ser.close()
