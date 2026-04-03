# The Architect: Senior Coding Agent (MSI Claw Edition)

An elite, local-first coding assistant and OpenClaw skill manager specifically engineered for the MSI Claw (Intel Core Ultra 7 155H).

This project bridges the gap between Windows-based Intel Arc GPU acceleration and Linux-based WSL development, providing a high-performance, low-latency coding mentor that runs entirely on your handheld hardware.

## 🚀 Quick Start: 'Field Mode' Ready

To get up and running on a fresh MSI Claw / WSL2 setup, run the automated setup script:

```bash
chmod +x setup_claw.sh
./setup_claw.sh
```

This script will:
1. Install system dependencies (`clinfo`, `libze-loader`).
2. Install **TruffleHog** and activate the **Git Pre-Push Hook** for security.
3. Create a virtual environment and install the **Intel-optimized AI stack** (Torch + IPEX).
4. Generate a `.env` template with optimal hardware settings.

## 🏎️ Hardware Optimization (Intel Arc & IPEX)

The Architect is configured to leverage the Intel Xᵉ-LPG graphics found in the Core Ultra 7. By default, it uses `dolphin-mistral:7b` (optimized via IPEX) for superior coding logic.

Critical environment variables used:
- `ONEAPI_DEVICE_SELECTOR=level_zero:0`: Forces execution on the Arc iGPU.
- `SYCL_ENABLE=1`: Enables the Data Parallel C++ runtime.
- `OLLAMA_NUM_GPU=999`: Offloads all model layers to the 8 Xe-cores.

## 🔒 Local-First & Private

- **Total Privacy:** Your code, logs, and conversations never leave your device.
- **Zero Latency:** No waiting for cloud API queues.
- **Offline Capable:** Ideal for 'Field Mode' development.

## 🛠️ MSI Claw Hardware Tuning (Essential)

For maximum inference speed, apply these settings in BIOS and MSI Center M:
1. **VRAM Allocation:** Set to 8GB.
2. **User Scenario:** Extreme Performance.
3. **Cooler Boost:** Recommended for heavy coding sessions.

## 📂 Project Structure (Modular)

- `coder_agent.py`: Entry point, Telegram bot polling.
- `handlers.py`: Command handlers (`/run`, `/install_skill`, `/whois`).
- `skill_manager.py`: Logic for sandbox execution and skill storage.
- `hardware_config.py`: Intel XPU / IPEX environment initialization.
- `git_utils.py`: Git automation (push/pull/status).
- `/skills`: Persistent directory for learned abilities.

## 📖 Documentation
Detailed guides are available in the [Wiki](wiki/Home.md).
