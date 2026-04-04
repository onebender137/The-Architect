@echo off
title The Architect - MSI Claw (Intel Arc Optimized)

:: ============================================================
:: INTEL ARC + OLLAMA GPU OPTIMIZATION
:: ============================================================
echo [1/3] Setting Intel Arc Environment...

:: Set your Ollama paths here
set OLLAMA_INTEL_GPU=true
set OLLAMA_NUM_GPU=999
set OLLAMA_FLASH_ATTENTION=true
set ZES_ENABLE_SYSMAN=1
set SYCL_ENABLE=1
set SYCL_CACHE_PERSISTENT=1
set ONEAPI_DEVICE_SELECTOR=level_zero:0
set OLLAMA_HOST=0.0.0.0

:: ============================================================
:: CLEAN START & OLLAMA INITIALIZATION
:: ============================================================
echo [2/3] Initializing Ollama...

taskkill /F /IM ollama.exe /T 2>nul
wsl --shutdown
timeout /t 3 /nobreak >nul

:: Start Ollama (Assumes default install or Ollama-Intel in path)
start /min "" ollama serve
timeout /t 10 /nobreak >nul

:: ============================================================
:: WSL LAUNCH
:: ============================================================
echo [3/3] Launching Architect in WSL...

:: Convert current Windows path to WSL path and launch
:: Assumes setup_claw.sh was run (env at ~/tg_bot_env)
wsl bash -c "export WSL_PATH=$(wslpath '%~dp0') && source ~/tg_bot_env/bin/activate && cd \"$WSL_PATH\" && python3 coder_agent.py"

pause
