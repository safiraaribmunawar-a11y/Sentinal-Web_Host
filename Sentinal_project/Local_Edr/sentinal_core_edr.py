import psutil
import time
import serial
import requests
import os
import threading
import hashlib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# --- CONFIG ---
CLOUD_URL = "https://sentinel-mesh.onrender.com/api/report"
COM_PORT = 'COM3' 
SECURITY_KEY = "admin123"
LAT, LON = 23.8103, 90.4125
WATCH_DIR = os.path.expanduser("~/Desktop") # Folder to watch for tampering

# --- GLOBAL STATE ---
file_baseline = {}
threat_active = False

# --- 1. FILE INTEGRITY (FIM) ENGINE ---
def get_file_hash(path):
    sha = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(4096): sha.update(chunk)
        return sha.hexdigest()
    except: return None

def build_fim_baseline():
    print(f"[*] Fingerprinting: {WATCH_DIR}...")
    for root, _, files in os.walk(WATCH_DIR):
        for name in files:
            path = os.path.join(root, name)
            file_baseline[path] = get_file_hash(path)

# --- 2. ASYNCHRONOUS CLOUD SYNC ---
def background_sync(status, mag):
    def run():
        try:
            requests.post(CLOUD_URL, json={"lat": LAT, "lon": LON, "magnitude": mag}, timeout=5)
        except: pass
    threading.Thread(target=run, daemon=True).start()

# --- 3. ADVANCED PROCESS TRACKER ---
def get_top_offender():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        processes.append(proc.info)
    # Sort by highest CPU usage
    top = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)
    return top[0] if top else None

# --- SETUP & AI TRAINING ---
build_fim_baseline()
scaler = StandardScaler()
model = IsolationForest(contamination=0.05, random_state=42)

print("[!] Learning System Baseline (20s)...")
train_data = []
for _ in range(20):
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    train_data.append([cpu, ram])

model.fit(scaler.transform(train_data))
print("✅ Baseline Locked. System Hardened.\n")

# --- MAIN EDR LOOP ---
try:
    while True:
        # A. Metric Capture
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        pred = model.predict(scaler.transform([[cpu, ram]]))[0]
        
        # B. Behavioral Analysis
        status = "SAFE"; mag = 25
        if pred == -1 or cpu > 90:
            offender = get_top_offender()
            status = "SEVERE" if cpu > 90 else "ELEVATED"
            mag = 350 if status == "SEVERE" else 150
            print(f"🚨 {status}: High usage by {offender['name']} (PID: {offender['pid']})")
        
        # C. Response Phase
        print(f"📊 CPU: {cpu}% | RAM: {ram}% | STATUS: {status}")
        background_sync(status, mag)
        
        # D. Security Verification (Blocking Call)
        if status == "SEVERE":
            start_t = time.time()
            while time.time() - start_t < 20:
                if input("ENTER KEY TO DISARM: ") == SECURITY_KEY:
                    print("✅ Identity Confirmed."); break
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[!] Shutdown.")
