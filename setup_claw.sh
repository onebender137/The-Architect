#!/bin/bash
# setup_claw.sh - MSI Claw Intel GPU Environment Setup (Intel Arc Optimized)
set -e

echo "🚀 Starting MSI Claw Environment Rebuild..."

# 1. Purge pip cache to remove potential NVIDIA or legacy artifacts
echo "[1/4] Purging pip cache..."
python3 -m pip cache purge

# 2. Recreate virtual environment (~/tg_bot_env)
echo "[2/4] Recreating virtual environment at ~/tg_bot_env..."
rm -rf ~/tg_bot_env
python3 -m venv ~/tg_bot_env

# 3. Activate environment and install Intel-optimized PyTorch/IPEX
# Note: Using the specific index URL for Intel XPU releases
echo "[3/4] Installing Intel-optimized PyTorch and IPEX (v2.5.1)..."
source ~/tg_bot_env/bin/activate
pip install --upgrade pip
pip install torch==2.5.1+cxx11.abi intel-extension-for-pytorch==2.5.10+xpu \
    --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

# 4. Verification of Intel Arc GPU
echo "[4/4] Validating Intel Arc GPU availability..."
python3 -c "import torch; import intel_extension_for_pytorch as ipex; \
    available = torch.xpu.is_available(); \
    device_name = torch.xpu.get_device_name(0) if available else 'None'; \
    print(f'\n✅ XPU Available: {available}'); \
    print(f'✅ Device Name: {device_name}\n')"

echo "🏁 Setup Complete! Your MSI Claw is now optimized for Intel Arc acceleration."
echo "To activate the environment, run: source ~/tg_bot_env/bin/activate"
