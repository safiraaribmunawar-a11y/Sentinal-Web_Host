"""
Sentinel Map Demo Script
Sends fake reports to test map colors on the dashboard.
Run this from your EDR terminal.
"""

import requests
import time

RENDER_URL = "https://sentinel-mesh.onrender.com"

def send_reports(country_name, lat, lon, count, severity="SEVERE"):
    print(f"\nSending {count} {severity} reports for {country_name}...")
    for i in range(count):
        try:
            requests.post(
                f"{RENDER_URL}/api/report",
                json={
                    "lat": lat,
                    "lon": lon,
                    "severity": severity,
                    "magnitude": 250,
                    "device_id": f"demo-{country_name.lower()}"
                },
                timeout=10
            )
            if (i + 1) % 10 == 0:
                print(f"  Sent {i + 1}/{count}")
        except Exception as e:
            print(f"  Error: {e}")
    print(f"Done! Check the map — {country_name} should now be colored.")

def clear_all():
    print("Clearing all reports...")
    requests.post(f"{RENDER_URL}/api/clear", timeout=10)
    print("Cleared!")

print("=" * 50)
print("  SENTINEL MAP DEMO")
print("=" * 50)
print("  1. Bangladesh — BLUE  (5 reports)")
print("  2. Bangladesh — YELLOW (55 reports)")
print("  3. Bangladesh — RED   (205 reports)")
print("  4. Russia     — BLUE  (5 reports)")
print("  5. Russia     — RED   (205 reports)")
print("  6. USA        — RED   (205 reports)")
print("  7. UK         — YELLOW (55 reports)")
print("  8. Custom country")
print("  9. Clear all reports")
print("=" * 50)

choice = input("Select [1-9]: ").strip()

if choice == "1":
    send_reports("Bangladesh", 23.81, 90.41, 5)
elif choice == "2":
    send_reports("Bangladesh", 23.81, 90.41, 55)
elif choice == "3":
    send_reports("Bangladesh", 23.81, 90.41, 205)
elif choice == "4":
    send_reports("Russia", 58.503, 81.818, 5)
elif choice == "5":
    send_reports("Russia", 58.503, 81.818, 205)
elif choice == "6":
    send_reports("USA", 40.71, -74.01, 205)
elif choice == "7":
    send_reports("UK", 51.51, -0.13, 55)
elif choice == "8":
    name = input("Country name: ")
    lat  = float(input("Latitude: "))
    lon  = float(input("Longitude: "))
    count = int(input("Number of reports: "))
    send_reports(name, lat, lon, count)
elif choice == "9":
    clear_all()
else:
    print("Invalid choice.")
