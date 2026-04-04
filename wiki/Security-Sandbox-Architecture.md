# 🔒 Security Sandbox Architecture

The Architect is designed with a "Local-First" approach, ensuring that your code, logs, and conversations remain private on your MSI Claw. To safely execute generated code, it uses a robust subprocess-based sandbox to prevent any accidental or malicious changes to your host operating system.

---

## 🛠️ Technical Implementation

The Architect's code execution engine is implemented in the `run_sandboxed_python` function in `skill_manager.py`. It uses a combination of Python's standard library modules to achieve isolation within a dedicated workspace.

### 1. Persistent `/workspace`

When a Python script is sent to The Architect, it doesn't run in the main project directory. Instead, it uses a dedicated `/workspace` directory for execution. This allows for persistent state during autonomous `/build` loops.

```python
temp_file = os.path.join(WORKSPACE_DIR, "task.py")
try:
    with open(temp_file, "w", encoding="utf-8") as f: f.write(code)
    # Execution occurs here...
except Exception as e:
    return False, f"❌ Workspace Error: {str(e)}"
```

**Key Security Features:**
- **Isolated CWD:** The root for execution is restricted to `/workspace`, not the project root.
- **Environment Passthrough:** Only necessary environment variables (like XPU/IPEX) are passed to the subprocess.

### 2. Execution via `subprocess`

The script is executed using `subprocess.run()`, which launches a new Python process separate from the main Telegram bot.

```python
process = subprocess.run(
    [sys.executable, temp_file],
    capture_output=True,
    text=True,
    timeout=10,
    cwd=temp_dir
)
```

**Resource Management:**
- **Timeout Protection:** The `timeout=10` parameter prevents scripts from hanging or consuming CPU resources indefinitely.
- **Output Buffering:** `capture_output=True` allows the bot to capture and return only the `stdout` and `stderr` of the script, rather than letting it output directly to the bot's logs.
- **Restricted CWD:** The `cwd=temp_dir` ensures the script's root is the temporary directory, not the main project folder.

### 3. Bash Safety Audits

Before executing any bash commands or installing new skills, The Architect uses its own LLM logic to perform a "Safety Audit." This audit specifically looks for destructive flags (e.g., `rm -rf`, `sudo`, or anything that might compromise the system).

---

## 🚀 Performance & Scaling

By running these sandboxed environments inside WSL, The Architect benefits from Linux-native execution speeds while still allowing the core application to manage the Windows environment and the Intel Arc GPU.
