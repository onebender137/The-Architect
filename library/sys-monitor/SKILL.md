# System & GPU Monitor (Intel Arc)

A diagnostic script that monitors top processes and Intel GPU telemetry directly from `/proc` and `/sys`.

## Capabilities
- Lists Top 5 CPU and Memory consuming processes.
- Reports Intel GPU Frequency and VRAM usage via `/sys/class/drm/`.
- Enhanced compatibility with multi-GPU and varied kernel paths for Intel Arc/Xe GPUs.

## Usage
```bash
python3 -c '
import os
import subprocess

def get_top_procs():
    print("--- Top 5 CPU Consumers ---")
    os.system("ps -eo pid,pcpu,comm --sort=-pcpu | head -n 6")
    print("\n--- Top 5 Memory Consumers ---")
    os.system("ps -eo pid,pmem,comm --sort=-pmem | head -n 6")

def get_intel_gpu():
    print("\n--- Intel Arc GPU Telemetry ---")

    # Common Intel GPU telemetry paths
    cards = ["/sys/class/drm/card0", "/sys/class/drm/card1"]
    freq_paths = ["device/clock_mhz", "gt/gt0/rp_cur_freq_mhz"]
    vram_paths = ["memory/used", "device/mem_used_mb"]

    found = False
    for card in cards:
        if os.path.exists(card):
            # Try Frequency
            freq = None
            for p in freq_paths:
                fpath = os.path.join(card, p)
                if os.path.exists(fpath):
                    with open(fpath, "r") as f:
                        freq = f.read().strip()
                        break

            # Try VRAM
            vram = None
            for p in vram_paths:
                vpath = os.path.join(card, p)
                if os.path.exists(vpath):
                    with open(vpath, "r") as f:
                        vram = f.read().strip()
                        break

            if freq or vram:
                print(f"Card: {os.path.basename(card)}")
                if freq: print(f"  GPU Frequency: {freq} MHz")
                if vram: print(f"  GPU VRAM Used: {vram} MB")
                found = True

    if not found:
        print("GPU: Intel DRM telemetry files not found in /sys/class/drm/ (or inaccessible).")

get_top_procs()
get_intel_gpu()
'
```

## Source
- Custom OpenClaw Implementation.
- GPU Telemetry Paths: https://github.com/nicolargo/glances/issues/994 and Intel kernel docs.
