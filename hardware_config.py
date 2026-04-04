import os
import logging

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
        # Detect Intel XPU (Arc GPU)
        device = "xpu" if torch.xpu.is_available() else "cpu"

        # Core Ultra NPU Integration (Detect via OpenVINO or ENV)
        npu_available = os.getenv("NPU_ENABLED", "false").lower() == "true"

        logger.info(f"Jules is waking up on: {device} (NPU: {npu_available})")
        if device == "xpu":
            logger.info(f"Hardware Verified: {torch.xpu.get_device_name(0)}")

        if npu_available:
            logger.info("Intel NPU Acceleration for OpenVINO GenAI active.")

        return device
    except ImportError:
        logger.warning("torch not found, defaulting to CPU mode.")
        return "cpu"
