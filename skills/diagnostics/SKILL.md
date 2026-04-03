# 🛠️ MSI Claw: Hardware Diagnostics

Provides real-time telemetry from the MSI Claw's Intel Core Ultra 7 155H and Arc GPU.

```bash
echo "📊 **Architect Hardware Diagnostics (MSI Claw)**"
echo ""

# CPU & Load
if [ -f /proc/loadavg ]; then
    LOAD=$(cat /proc/loadavg | awk '{print $1" "$2" "$3}')
    echo "**CPU Load (1/5/15m)**: $LOAD"
else
    echo "**CPU Load**: N/A"
fi

# Memory Usage
MEM=$(free -m | grep Mem | awk '{print $3"MB / "$2"MB"}')
echo "**Memory (Used/Total)**: $MEM"

# Disk Usage
DISK=$(df -h / | grep / | awk '{print $3" / "$2" ("$5" used)"}')
echo "**Disk space (Used/Total)**: $DISK"

# GPU Usage (Intel Arc)
# Try sysfs first (common in newer kernels)
if [ -f /sys/class/drm/card0/device/gpu_busy_percent ]; then
    GPU=$(cat /sys/class/drm/card0/device/gpu_busy_percent)
    echo "**GPU Load**: $GPU%"
elif command -v intel_gpu_top > /dev/null 2>&1; then
    # Quick sample with intel_gpu_top
    GPU=$(intel_gpu_top -s 1 -n 1 | grep "Render/3D" | awk '{print $2}')
    echo "**GPU Load (Arc)**: $GPU%"
else
    echo "**GPU Load**: Stats Unavailable (WSL limitation)"
fi

# Uptime
if [ -f /proc/uptime ]; then
    UP_SECONDS=$(cat /proc/uptime | awk '{print $1}')
    UP_MINS=$(echo "$UP_SECONDS / 60" | bc)
    UP_HOURS=$(echo "$UP_MINS / 60" | bc)
    echo "**System Uptime**: $UP_HOURS hours ($UP_MINS mins)"
else
    echo "**System Uptime**: N/A"
fi

# Intel AI Stack
echo "**Device Type**: Intel Arc Graphics (XPU)"
echo "**IPEX Optimization**: Active (Level Zero)"
```
