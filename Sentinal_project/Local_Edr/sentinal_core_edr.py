import psutil
import time
import serial
import requests
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

COM_PORT = 'COM3' 
BAUD_RATE = 9600
CLOUD_URL = "https://sentinel-global.onrender.com/api/report"
SECURITY_KEY = "admin123"

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(3) 
    print(f"Hardware Connected on {COM_PORT}")
except Exception as e:
    print(f"Hardware not found: {e}")
    ser = None

scaler = StandardScaler()
model = IsolationForest(contamination=0.05, random_state=42)

def get_metrics():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    net1 = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    time.sleep(0.5) 
    net2 = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    return [cpu, ram, (net2 - net1)]

def upload_to_cloud(status, cpu, ram):
    try:
        requests.post(CLOUD_URL, json={"status": status, "cpu": cpu, "ram": ram}, timeout=1)
    except:
        pass

def send_to_arduino(status):
    if ser:
        try:
            ser.write(f"{status}\n".encode())
        except: pass

print("\nSentinelCore: Learning System Baseline...")
training_data = []
for i in range(20):
    m = get_metrics()
    training_data.append(m)
    print(f"Snap {i+1}/20: {m}")

training_data = np.array(training_data)
scaler.fit(training_data)
model.fit(scaler.transform(training_data))
print("Baseline Locked.")
try:
    while True:
        raw_m = get_metrics()
        scaled_m = scaler.transform([raw_m])
        prediction = model.predict(scaled_m)[0]
        
        cpu, ram, net = raw_m
        score = 0
        if cpu > 85: score += 1
        if ram > 85: score += 1
        if prediction == -1: score += 1
        
        status = "SAFE"
        if cpu > 98 or score >= 2: status = "SEVERE"
        elif score == 1: status = "ELEVATED"

        print(f"📊 CPU: {cpu}% | RAM: {ram}% | ANOMALY: {prediction==-1} | STATUS: {status}")
        
        send_to_arduino(status)
        upload_to_cloud(status, cpu, ram)

        if status == "SEVERE":
            print("🚨 SEVERE THREAT DETECTED! Starting 20s Verification Timer...")
            start_time = time.time()
            verified = False
            
            while time.time() - start_time < 20:
                upload_to_cloud("SEVERE", cpu, ram)
                
                # Manual entry
                key = input("ENTER SECURITY KEY TO DISARM: ")
                if key == SECURITY_KEY:
                    print("Identity Verified. System Reset.")
                    verified = True
                    break
                else:
                    print("Access Denied.")
            
            if not verified:
                print("⚠️ VERIFICATION TIMEOUT! System Locked in SEVERE mode.")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n Shutdown.")
    if ser: ser.close()