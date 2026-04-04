import os
import logging
import os.path

logger = logging.getLogger(__name__)

# ====================== HARDWARE SETUP (MSI Claw / Intel Arc XPU) ======================
def setup_hardware():
    os.environ["ONEAPI_DEVICE_SELECTOR"] = "level_zero:0"
    os.environ["UR_L0_LOADER_IGNORE_VERSION"] = "1"

    wsl_path = "/usr/lib/wsl/lib"
    if wsl_path not in os.environ.get("LD_LIBRARY_PATH", ""):
        os.environ["LD_LIBRARY_PATH"] = f"{wsl_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

    try:
        import torch
        # Detect Intel XPU
        device = "xpu" if torch.xpu.is_available() else "cpu"
        logger.info(f"Jules is waking up on: {device}")
        if device == "xpu":
            logger.info(f"Hardware Verified: {torch.xpu.get_device_name(0)}")
        return device
    except ImportError:
        logger.warning("torch not found, defaulting to CPU mode.")
        return "cpu"

def get_power_stats():
    """Retrieves battery and thermal stats, with WSL2-compatible fallbacks."""
    stats = {"battery": "N/A", "thermal": "N/A"}

    # Battery Check (WSL2 often lacks direct access, so we try common paths)
    battery_path = "/sys/class/power_supply/BAT0/capacity"
    if os.path.exists(battery_path):
        try:
            with open(battery_path, "r") as f:
                stats["battery"] = f"{f.read().strip()}%"
        except Exception:
            pass

    # Thermal Check (Common thermal zones)
    thermal_path = "/sys/class/thermal/thermal_zone0/temp"
    if os.path.exists(thermal_path):
        try:
            with open(thermal_path, "r") as f:
                temp_milli = int(f.read().strip())
                stats["thermal"] = f"{temp_milli // 1000}°C"
        except Exception:
            pass

    return stats
