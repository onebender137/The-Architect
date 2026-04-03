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
sudo apt install -y python3-venv libze-loader clinfo curl

# 3. Security: TruffleHog & Git Hooks
echo "🛡️ Setting up security protocols..."
if ! command -v trufflehog &> /dev/null; then
    echo "📥 Installing TruffleHog..."
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
else
    echo "✅ TruffleHog already installed."
fi

if [ -f "scripts/pre-push" ]; then
    echo "⚓ Installing git pre-push hook..."
    cp scripts/pre-push .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
    echo "✅ Pre-push hook active."
else
    echo "⚠️ scripts/pre-push not found, skipping hook setup."
fi

# 4. Environment Management
VENV_PATH="$HOME/tg_bot_env"
if [ -d "$VENV_PATH" ]; then
    echo "♻️ Refreshing existing virtual environment at $VENV_PATH..."
    rm -rf "$VENV_PATH"
fi

echo "🏗️ Creating fresh virtual environment at $VENV_PATH..."
python3 -m venv "$VENV_PATH"

# 5. Python Package Installation
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
    torchvision==0.18.1.post0+xpu \
    torchaudio==2.3.1.post0+xpu \
    intel-extension-for-pytorch==2.3.110+xpu \
    --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

# 6. GPU Driver & AI Stack Verification
echo "🔍 Verifying GPU Visibility & AI Heartbeat..."

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

# 7. OneAPI/IPEX Configuration (.env)
echo "📝 Generating local .env configuration..."
if [ -f .env ]; then
    echo "⚠️  .env already exists. Merging new Arc variables while preserving existing config..."
    # Append Arc variables if they don't exist
    for var in ONEAPI_DEVICE_SELECTOR SYCL_ENABLE OLLAMA_NUM_GPU ZES_ENABLE_SYSMAN SYCL_CACHE_PERSISTENT MODEL_NAME OLLAMA_URL UR_L0_LOADER_IGNORE_VERSION OLLAMA_FLASH_ATTENTION; do
        if ! grep -q "^$var=" .env; then
            case $var in
                ONEAPI_DEVICE_SELECTOR) echo "ONEAPI_DEVICE_SELECTOR=level_zero:0" >> .env ;;
                SYCL_ENABLE) echo "SYCL_ENABLE=1" >> .env ;;
                OLLAMA_NUM_GPU) echo "OLLAMA_NUM_GPU=999" >> .env ;;
                ZES_ENABLE_SYSMAN) echo "ZES_ENABLE_SYSMAN=1" >> .env ;;
                SYCL_CACHE_PERSISTENT) echo "SYCL_CACHE_PERSISTENT=1" >> .env ;;
                MODEL_NAME) echo "MODEL_NAME=dolphin-mistral:7b" >> .env ;;
                OLLAMA_URL) echo "OLLAMA_URL=http://172.25.64.1:11434" >> .env ;;
                UR_L0_LOADER_IGNORE_VERSION) echo "UR_L0_LOADER_IGNORE_VERSION=1" >> .env ;;
                OLLAMA_FLASH_ATTENTION) echo "OLLAMA_FLASH_ATTENTION=true" >> .env ;;
            esac
        fi
    done
else
    cat <<EOF > .env
# --- The Architect: Telegram Bot Configuration ---
BOT_TOKEN="your_telegram_bot_token_here"
MODEL_NAME=dolphin-mistral:7b
OLLAMA_URL=http://172.25.64.1:11434

# --- The Architect: Intel Arc Optimized Environment ---
ONEAPI_DEVICE_SELECTOR=level_zero:0
SYCL_ENABLE=1
OLLAMA_NUM_GPU=999
ZES_ENABLE_SYSMAN=1
SYCL_CACHE_PERSISTENT=1
UR_L0_LOADER_IGNORE_VERSION=1
OLLAMA_FLASH_ATTENTION=true
EOF
fi

echo "-------------------------------------------------------"
echo "🏁 Setup Complete!"
echo "✅ Virtual Environment: $VENV_PATH"
echo "✅ Local .env file updated/generated."
echo "💡 To use: source $VENV_PATH/bin/activate && python coder_agent.py"
echo "-------------------------------------------------------"
