# 🏎️ Ollama Optimization for dolphin-mistral:7b (Intel XPU)

To maximize the tokens-per-second (TPS) on the MSI Claw's Intel Arc GPU, use the following configuration for `dolphin-mistral:7b`.

## 🛠️ Optimal Modelfile Parameters

Create or update your Modelfile with these settings:

```dockerfile
FROM dolphin-mistral:7b

# Offload all layers to the Intel Arc GPU
PARAMETER num_gpu 999

# Optimize context window for memory efficiency (default 4096)
PARAMETER num_ctx 4096

# Threads should match physical cores for best performance
# Core Ultra 7 155H has 6 P-cores
PARAMETER num_thread 6

# Sampling parameters for consistent speed
PARAMETER temperature 0.7
PARAMETER top_p 0.9
```

## 🌍 Environment Variables

These are automatically added or merged into your `.env` by `setup_claw.sh`:

**Key Variables:**
- `ONEAPI_DEVICE_SELECTOR=level_zero:0`: Forces the Level Zero driver for Intel GPU.
- `SYCL_ENABLE=1`: Enables SYCL runtime for IPEX.
- `ZES_ENABLE_SYSMAN=1`: Allows GPU power management.

**Performance Boosters:**
- `OLLAMA_NUM_GPU=999`: Double-checks layer offloading.
- `UR_L0_LOADER_IGNORE_VERSION=1`: Prevents driver version mismatch errors.

## 📊 Expected Performance

With these optimizations, `dolphin-mistral:7b` (Q4_0) should achieve:
- **Prompt Processing:** ~50-80 tokens/sec
- **Token Generation:** ~25-40 tokens/sec

*Note: Performance may vary based on MSI Center M power profile (Extreme Performance is recommended).*
