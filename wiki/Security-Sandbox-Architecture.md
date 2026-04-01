# 🔒 Security Sandbox Architecture

The Architect is designed with a "Local-First" approach, ensuring that your code, logs, and conversations remain private on your MSI Claw. To safely execute generated code, it uses a robust subprocess-based sandbox to prevent any accidental or malicious changes to your host operating system.

---

## 🛠️ Technical Implementation

The Architect's code execution engine is implemented in the `run_sandboxed_python` function in `coder_agent.py`. It uses a combination of Python's standard library modules to achieve isolation.

### 1. Isolation via `tempfile`

When a Python script is sent to The Architect, it doesn't run in the current working directory. Instead, it uses `tempfile.mkdtemp()` to create a completely isolated, temporary directory for each execution.

```python
temp_dir = tempfile.mkdtemp()
temp_file = os.path.join(temp_dir, "task.py")
try:
    with open(temp_file, "w", encoding="utf-8") as f: f.write(code)
    # Execution occurs here...
finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
```

**Key Security Features:**
- **No Shared State:** Each execution starts with a clean, empty directory.
- **Automatic Cleanup:** The `finally` block ensures the temporary directory and all generated files are deleted immediately after the script finishes, regardless of whether it succeeded or failed.

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
