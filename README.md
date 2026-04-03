The Architect: Senior Coding Agent (MSI Claw Edition)

An elite, local-first coding assistant and OpenClaw skill manager specifically engineered for the MSI Claw (Intel Core Ultra 7 155H).

This project bridges the gap between Windows-based Intel Arc GPU acceleration and Linux-based WSL development, providing a high-performance, low-latency coding mentor that runs entirely on your handheld hardware.

🏎️ Hardware & Model (Intel Arc & Dolphin-Mistral)

The Architect has been upgraded to **Dolphin-Mistral 7B** to provide superior coding logic and reduced output restrictions. It is fully optimized for the Intel Xᵉ-LPG graphics (8 Xe-cores) found in the MSI Claw's Core Ultra 7 155H.

The system utilizes **Intel IPEX** (Intel Extension for PyTorch) optimizations to ensure all inference occurs on the XPU:

ONEAPI_DEVICE_SELECTOR=level_zero:0: Forces execution on the Arc iGPU.

SYCL_ENABLE=1: Enables the Data Parallel C++ runtime for cross-architecture speed.

OLLAMA_NUM_GPU=999: Offloads all model layers to the 8 Xe-cores for maximum inference speed.

ZES_ENABLE_SYSMAN=1: Allows the system to manage GPU power states for sustained performance.

🔒 Local-First & Private

Unlike Cloud-based AI assistants, The Architect is designed to run on a local Ollama instance.

Total Privacy: Your code, logs, and conversations never leave your device or local network.

Zero Latency: No waiting for cloud API queues.

Offline Capable: Code and manage your projects without an internet connection.

🛠️ MSI Claw Hardware Tuning (Essential)

For maximum inference speed (tokens per second), your Claw needs specific BIOS and system tweaks to prevent thermal throttling and power capping:

1. BIOS Adjustments (Advanced Menu)

VRAM Allocation: Set to 8GB (or "Auto" if using the latest BIOS update) to ensure Ollama has enough memory to load the 7B model entirely on the GPU.

CPU Power Limits (PL1/PL2): Ensure these are set to allow for the 28W-45W range to handle both the LLM and the WSL overhead.

2. MSI Center M Fixes

User Scenario: Set to Extreme Performance.

GPU Overclock: Avoid aggressive core offsets; the IPEX runtime prefers stability for SYCL kernels.

Cooler Boost: Recommended during long coding sessions or when installing heavy skills to keep the Core Ultra 7 in the boost clock range.

🔗 Essential Resources & Downloads

To achieve the hardware acceleration described above, you must use the Intel-specific builds of these tools:

Intel-Optimized Ollama (IPEX): Download from Intel's official GitHub

Intel® oneAPI Base Toolkit: Download here

Intel Arc Graphics Drivers: Ensure you are on the latest "Game On" drivers.

🚀 Key Features

Intel Arc Optimized: Custom Windows-to-WSL bridge ensures the LLM runs on the GPU, not the CPU.

Secure Subprocess Sandbox: Executes generated Python code in isolated temporary directories.

OpenClaw Skill Manager: A modular system to install, audit, and run skills via Telegram.

Self-Healing Loop: Automatically monitors execution errors and writes its own hotfixes.

📂 Project Structure

coder_agent.py: The core asynchronous Telegram bot and logic engine.

launch_architect.bat: The "Special Sauce" launcher for MSI Claw hardware.

requirements.txt: Python dependencies.

/skills: A persistent directory for your Architect's learned abilities.

.env: (Hidden) Stores your private bot token.