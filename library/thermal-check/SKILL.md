# Thermal & Throttling Health (Intel)

Monitors Intel CPU temperatures and checks for thermal throttling events using kernel sysfs interfaces.

## Capabilities
- Reads package and core temperatures via `/sys/class/thermal`.
- Detects if the system is currently thermal throttling.
- Ideal for diagnosing performance drops on the MSI Claw.

## Usage
```bash
python3 -c '
import os
import glob

def get_temp():
    print("--- CPU Thermal Status ---")
    zones = glob.glob("/sys/class/thermal/thermal_zone*")
    for zone in zones:
        try:
            with open(os.path.join(zone, "type"), "r") as f:
                ztype = f.read().strip()
            with open(os.path.join(zone, "temp"), "r") as f:
                temp = int(f.read().strip()) / 1000
            print(f"{ztype}: {temp:.1f}°C")
        except:
            continue

def check_throttling():
    print("\n--- Throttling Status ---")
    # Paths for Intel Core processors
    throttle_files = glob.glob("/sys/devices/system/cpu/cpu*/thermal_throttle/*_throttle_count")
    total_throttles = 0
    for tf in throttle_files:
        try:
            with open(tf, "r") as f:
                total_throttles += int(f.read().strip())
        except:
            continue

    if total_throttles > 0:
        print(f"WARNING: Detected {total_throttles} historical throttling events across cores.")
    else:
        print("Status: No throttling events detected.")

get_temp()
check_throttling()
'
```

## Source
- Custom OpenClaw Implementation.
- Reference: https://community.netbeez.net/t/cpu-temperature-monitoring-script/298
