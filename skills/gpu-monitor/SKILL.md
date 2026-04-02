# 📊 GPU Monitoring for MSI Claw

A bash-based skill to monitor GPU utilization and thermal metrics directly from the terminal.

## 🚀 Execution
Execute using `/run_skill gpu-monitor`.

```bash
#!/bin/bash

echo "📊 --- MSI Claw (Intel Arc) Hardware Monitoring --- 📊"

# Check for intel_gpu_top (requires intel-gpu-tools)
if command -v intel_gpu_top >/dev/null 2>&1; then
    echo "🔍 Intel GPU Stats (Snapshot):"
    intel_gpu_top -s 1 -n 1 | grep -E "Render/3D|Video|Blitter"
else
    # Fallback to sysfs if available (kernel dependent)
    GPU_BUSY="/sys/class/drm/card0/device/gpu_busy_percent"
    if [ -f "$GPU_BUSY" ]; then
        echo "🔥 GPU Utilization: $(cat $GPU_BUSY)%"
    else
        echo "⚠️ GPU: No direct sysfs metric found. Please install 'intel-gpu-tools'."
    fi
fi

# CPU & Memory Fallback (The Architect is always working)
echo "💻 CPU Load: $(awk '{print $1, $2, $3}' /proc/loadavg)"
echo "🧠 RAM Available: $(grep MemAvailable /proc/meminfo | awk '{print $2/1024 " MB"}')"

# Thermal Monitoring
THERMAL_DIR="/sys/class/thermal"
if [ -d "$THERMAL_DIR" ]; then
    echo "🌡️ Thermals:"
    for zone in $THERMAL_DIR/thermal_zone*; do
        TYPE=$(cat $zone/type)
        TEMP=$(cat $zone/temp)
        echo "   - $TYPE: $((TEMP/1000))°C"
    done
fi

echo "📊 --- End of Snapshot --- 📊"
```
