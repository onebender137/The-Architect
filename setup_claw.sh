#!/bin/bash

# setup_claw.sh - MSI Claw Optimization & Environment Setup
# Specifically for Intel Core Ultra 7 155H + Arc iGPU

echo "🚀 Starting MSI Claw Setup for The Architect..."

# 1. Pip Cache Purge (Remove old NVIDIA/conflicting files)
echo "🧹 Purging pip cache to remove old NVIDIA-specific artifacts..."
pip cache purge

# 2. Environment Variables for Intel GPU Acceleration (WSL-side)
echo "⚙️ Configuring Intel IPEX / SYCL Environment..."
export ONEAPI_DEVICE_SELECTOR=level_zero:0
export SYCL_ENABLE=1
export ZES_ENABLE_SYSMAN=1
export OLLAMA_NUM_GPU=999

# 3. Installing Dependencies
echo "📦 Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# 4. Creating Skills Directory (if missing)
if [ ! -d "skills" ]; then
    echo "📁 Creating skills directory..."
    mkdir -p skills
fi

# 5. Verification
echo "✅ Setup Complete!"
echo "--------------------------------------------------------"
echo "HARDWARE TRACE:"
if command -v lspci > /dev/null; then
    lspci | grep -i "VGA\|Display"
else
    echo "Note: Install 'pciutils' to see GPU hardware trace."
fi
echo "--------------------------------------------------------"
echo "Ready to run: python3 coder_agent.py"
