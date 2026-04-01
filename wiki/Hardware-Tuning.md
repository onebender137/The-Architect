# 🏎️ Hardware Tuning

For maximum inference speed (tokens per second) on the MSI Claw, the system requires specific BIOS and system-level tweaks to prevent thermal throttling and power capping. This page details the configuration for the Intel Core Ultra 7 155H and its integrated Intel Arc GPU.

---

## 1. BIOS Adjustments (Advanced Menu)

- **VRAM Allocation:** Set to 8GB (or "Auto" if using the latest BIOS update) to ensure Ollama has enough memory to load the 7B model entirely on the GPU.
- **CPU Power Limits (PL1/PL2):** Ensure these are set to allow for the 28W-45W range to handle both the LLM and the WSL overhead.

## 2. MSI Center M Fixes

- **User Scenario:** Set to **Extreme Performance**.
- **GPU Overclock:** Avoid aggressive core offsets; the IPEX runtime prefers stability for SYCL kernels.
- **Cooler Boost:** Recommended during long coding sessions or when installing heavy skills to keep the Core Ultra 7 in its boost clock range.

## 3. Intel Arc & IPEX Optimization

The Architect uses Intel IPEX (Intel Extension for PyTorch/Ollama) to leverage the 8 Xᵉ-cores of the Core Ultra 7. The following environment variables are automatically configured in `launch_architect.bat` to optimize performance:

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `ONEAPI_DEVICE_SELECTOR` | `level_zero:0` | Forces execution on the Arc iGPU. |
| `SYCL_ENABLE` | `1` | Enables the Data Parallel C++ runtime for cross-architecture speed. |
| `OLLAMA_NUM_GPU` | `999` | Offloads all model layers to the GPU for maximum inference speed. |
| `ZES_ENABLE_SYSMAN` | `1` | Allows the system to manage GPU power states for sustained performance. |
| `SYCL_CACHE_PERSISTENT` | `1` | Persists compiled kernels to speed up subsequent launches. |
| `OLLAMA_FLASH_ATTENTION` | `true` | Enables Flash Attention for faster processing of long contexts. |

## 🔗 Essential Resources & Downloads

To achieve the hardware acceleration described above, you must use the Intel-specific builds of these tools:

- [**Intel-Optimized Ollama (IPEX)**](https://github.com/intel/ollama/releases): Download from Intel's official GitHub repository.
- [**Intel® oneAPI Base Toolkit**](https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html): Essential for the SYCL runtime.
- [**Intel Arc Graphics Drivers**](https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html): Ensure you are on the latest "Game On" drivers.
