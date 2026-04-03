# 🛠️ MSI Claw Hardware Diagnostics

This skill provides a deep dive into the MSI Claw's current hardware state, prioritizing Intel Arc GPU metrics.

```bash
echo "--- 🖥️ MSI Claw Diagnostics ---"
echo "Date: $(date)"
echo "Uptime: $(uptime -p)"
echo ""

echo "--- 🏎️ GPU Status (Intel Arc) ---"
if command -v intel_gpu_top > /dev/null; then
    timeout 1s intel_gpu_top -s 1000 -n 1 | head -n 15
else
    echo "intel_gpu_top not found. Checking sysfs..."
    if [ -f /sys/class/drm/card0/device/gpu_busy_percent ]; then
        echo "GPU Load: $(cat /sys/class/drm/card0/device/gpu_busy_percent)%"
    else
        echo "GPU sysfs metrics unavailable in WSL2."
    fi
fi
echo ""

echo "--- 🧠 CPU & RAM Status ---"
echo "Load Average: $(cat /proc/loadavg)"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo ""

echo "--- 🌡️ Thermals ---"
for thermal in /sys/class/thermal/thermal_zone*; do
    if [ -f "$thermal/temp" ]; then
        type=$(cat "$thermal/type")
        temp=$(cat "$thermal/temp")
        echo "$type: $((temp/1000))°C"
    fi
done

if [ -z "$(ls /sys/class/thermal/thermal_zone* 2>/dev/null)" ]; then
    echo "Thermal sysfs paths empty (Normal for some WSL2 distros)."
fi
echo "------------------------------"
```
