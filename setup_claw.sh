#!/bin/bash

# 🏎️ The Architect: MSI Claw WSL2 Auto-Setup
# Engineered for Intel Core Ultra 7 155H (Intel Arc Graphics)

set -e

echo "-------------------------------------------------------"
echo "🚀 Starting The Architect Setup for MSI Claw (WSL2)"
echo "-------------------------------------------------------"

# 1. WSL Detection
if ! grep -qi microsoft /proc/version; then
    echo "❌ Error: This script is precision-tuned for WSL2 on MSI Claw."
    echo "   Aborting to prevent contamination of standard Linux environments."
    exit 1
fi
echo "✅ WSL2 Environment Confirmed."

# 2. System Dependencies (APT Heavy Lifting)
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3-venv libze-loader clinfo intel-gpu-tools

# 3. Environment Management
VENV_PATH="$HOME/tg_bot_env"
if [ -d "$VENV_PATH" ]; then
    echo "♻️ Refreshing existing virtual environment at $VENV_PATH..."
    rm -rf "$VENV_PATH"
fi

echo "🏗️ Creating fresh virtual environment at $VENV_PATH..."
python3 -m venv "$VENV_PATH"

# 4. Python Package Installation
echo "🐍 Updating pip and installing standard requirements..."
"$VENV_PATH/bin/pip" install --upgrade pip

if [ -f "requirements.txt" ]; then
    "$VENV_PATH/bin/pip" install -r requirements.txt
else
    echo "⚠️ requirements.txt not found, skipping standard dependencies."
fi

echo "🚀 Installing Intel-optimized AI stack (Torch + IPEX)..."
# Using Intel's XPU-specific stable release URL
"$VENV_PATH/bin/pip" install torch==2.3.1.post0+xpu \
    intel-extension-for-pytorch==2.3.110+xpu \
    --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

# 5. GPU Driver & AI Stack Verification
echo "🔍 Verifying GPU Visibility & AI Heartbeat..."

# Check intel_gpu_top
if command -v intel_gpu_top >/dev/null 2>&1; then
    echo "✅ intel_gpu_top detected."
    intel_gpu_top -s 1 -n 1 | grep -E "Render/3D|Video|Blitter" || true
else
    echo "⚠️ intel_gpu_top not found. Ensure 'intel-gpu-tools' is installed."
fi

# Check D3D12 Bridge
if [ -e /dev/dxg ]; then
    echo "✅ /dev/dxg (D3D12 Bridge) is visible."
else
    echo "❌ /dev/dxg not found! Ensure WSLg is enabled and Intel drivers are updated on Windows."
fi

# Run IPEX Verification
echo "📊 Running IPEX/XPU Heartbeat Check..."
"$VENV_PATH/bin/python3" -c "
try:
    import torch
    import intel_extension_for_pytorch as ipex
    xpu_available = torch.xpu.is_available()
    print(f'✅ PyTorch + IPEX Loaded.')
    print(f'✅ XPU available: {xpu_available}')
    if xpu_available:
        print(f'   Device Name: {torch.xpu.get_device_name(0)}')
    else:
        print('❌ XPU is NOT available to PyTorch.')
except ImportError as e:
    print(f'❌ Failed to import AI stack: {e}')
except Exception as e:
    print(f'❌ Verification Error: {e}')
"

# 6. OneAPI/IPEX Configuration (.env)
echo "📝 Configuring local .env for Intel Arc..."
ENV_FILE=".env"

# List of hardware variables to ensure exist
vars=(
    "ONEAPI_DEVICE_SELECTOR=level_zero:0"
    "SYCL_ENABLE=1"
    "OLLAMA_NUM_GPU=999"
    "ZES_ENABLE_SYSMAN=1"
    "SYCL_CACHE_PERSISTENT=1"
    "OLLAMA_FLASH_ATTENTION=true"
)

if [ ! -f "$ENV_FILE" ]; then
    echo "📄 .env not found. Creating from template..."
    if [ -f ".env.template" ]; then
        cp .env.template "$ENV_FILE"
    else
        touch "$ENV_FILE"
    fi
fi

for var in "${vars[@]}"; do
    key=$(echo "$var" | cut -d'=' -f1)
    if ! grep -q "^$key=" "$ENV_FILE"; then
        echo "➕ Adding $var to $ENV_FILE"
        echo "$var" >> "$ENV_FILE"
    else
        echo "✅ $key already configured."
    fi
done

# 7. Security & Secret Scanning (TruffleHog)
echo "🛡️ Configuring security hooks..."
if ! command -v trufflehog &> /dev/null; then
    echo "🔍 TruffleHog not found. Attempting installation..."
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin || echo "⚠️ TruffleHog installation failed. Please install manually."
fi

if [ -f "scripts/pre-push" ]; then
    mkdir -p .git/hooks
    cp scripts/pre-push .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
    echo "✅ Git pre-push hook installed."
else
    echo "⚠️ scripts/pre-push not found. Skipping hook installation."
fi

echo "-------------------------------------------------------"
echo "🏁 Setup Complete!"
echo "✅ Virtual Environment: $VENV_PATH"
echo "✅ Local .env file generated in project root."
echo "💡 To use: source $VENV_PATH/bin/activate && python coder_agent.py"
echo "-------------------------------------------------------"
