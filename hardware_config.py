import os
import torch
import logging

logger = logging.getLogger(__name__)

# ====================== HARDWARE SETUP (MSI Claw / Intel Arc XPU) ======================
def setup_hardware():
    os.environ["ONEAPI_DEVICE_SELECTOR"] = "level_zero:0"
    os.environ["UR_L0_LOADER_IGNORE_VERSION"] = "1"

    wsl_path = "/usr/lib/wsl/lib"
    if wsl_path not in os.environ.get("LD_LIBRARY_PATH", ""):
        os.environ["LD_LIBRARY_PATH"] = f"{wsl_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

    # Detect Intel XPU
    device = "xpu" if torch.xpu.is_available() else "cpu"
    logger.info(f"Jules is waking up on: {device}")
    if device == "xpu":
        logger.info(f"Hardware Verified: {torch.xpu.get_device_name(0)}")
    return device
