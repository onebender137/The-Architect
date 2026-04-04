# 🏗️ The Architect: Senior Coding Agent (Syndicate Build)

**The Architect** is an elite, local-first coding assistant and OpenClaw skill manager specifically engineered for the **MSI Claw (Intel Core Ultra 7 155H)**.

The Architect represents the **Neural Foundry Build (Phase 9)**, bridging the gap between Windows-based Intel Arc GPU acceleration and Linux-based WSL development. It provides a high-performance, low-latency coding mentor that runs entirely on your handheld hardware.

---

## 🧪 Phase 9: The Neural Foundry (Latest Features)

The **Neural Foundry Build** focuses on agentic autonomy and hardware-aware intelligence:

*   🕸️ **Agentic Graph Memory:** Moving beyond flat RAG to a dependency-mapped knowledge graph of your entire codebase.
*   🔋 **Power-Aware Telemetry:** Real-time battery and thermal monitoring to drive adaptive AI inference.
*   🤖 **Swarm Orchestration:** Concurrent multi-agent collaboration (Ghost, Pulse, Spark) for complex build tasks.
*   ⚡ **OpenVINO GenAI Core:** High-performance, NPU-optimized inference backend specifically for Intel Core Ultra.

---

## 🧠 Phase 6: The Neural Expansion

The **Syndicate Build** introduces heavy-duty autonomous and contextual capabilities:

*   🧠 **Neural Memory (Local RAG):** Persistent codebase awareness using ChromaDB and `all-MiniLM-L6-v2`. Use `/reindex` to scan your project.
*   🤖 **Autonomous Task Agent:** The `/build` loop allows The Architect to execute multi-turn coding tasks, self-heal from errors, and persist work in a dedicated `/workspace`.
*   🎙️ **Voice-to-Code:** Local **OpenAI Whisper** integration (running on XPU) for hands-free coding and commanding via Telegram voice messages.
*   📟 **Claw HUD & Diagnostics:** Real-time BBS-style ASCII telemetry and deep-dive hardware monitoring optimized for the MSI Claw's 7-inch screen.

---

## 🏎️ Hardware & Model (Intel Arc & Dolphin-Mistral)

The Architect utilizes **Dolphin-Mistral 7B**, optimized for the Intel Xᵉ-LPG graphics (8 Xe-cores) found in the MSI Claw.

*   **Intel IPEX Optimization:** Uses Intel Extension for PyTorch to offload inference to the Arc iGPU.
*   **Unrestricted Logic:** Dolphin-Mistral provides maximum flexibility for complex technical requests without censorship.
*   **Mobile Optimized:** All outputs are formatted for the MSI Claw's screen (50-char width, vertical lists instead of tables).

---

## 🚀 Quick Start (MSI Claw / WSL2)

1.  **Clone the Repo** into your WSL2 environment.
2.  **Run the Auto-Setup:**
    ```bash
    chmod +x setup_claw.sh
    ./setup_claw.sh
    ```
    *This script installs system dependencies, configures the Intel AI stack (Torch/IPEX), and generates your `.env` template.*
3.  **Configure `.env`:** Add your `BOT_TOKEN` (from @BotFather).
4.  **Launch:**
    ```bash
    source ~/tg_bot_env/bin/activate
    python coder_agent.py
    ```

---

## 🕹️ Command Menu

| Command | Description |
| :--- | :--- |
| `/build [task]` | **Start Autonomous Build Loop** (5 iterations max) |
| `/reindex` | **Refresh Neural Memory** (RAG) by scanning codebase |
| `/run [code]` | Execute Python in a secure, persistent `/workspace` |
| `/scan` | Generate a visual tree of the project structure |
| `/hud` | Display real-time ASCII hardware telemetry |
| `/stats` | View engine, device, and RAG status |
| `/install_skill` | Add a modular OpenClaw skill (with safety audit) |
| `/run_skill [slug]` | Execute an installed bash-based skill |
| `/promote [file]` | Graduate a script from `/library` to a modular skill |
| `/ingest [file]` | Read a specific file into the current conversation context |
| `/logs` | View the last 10 lines of the bot's runtime logs |
| `/whois` | Display user identification (SYSOP handle) |
| `/commit [msg]` | Stage, commit, and push changes to Git |

---

## 🛠️ Deep Dive Features

### 🧠 Neural Memory (RAG)
The Architect doesn't just "see" what you paste; it understands your entire project. Using **ChromaDB**, it indexes your `.py`, `.md`, and `.sh` files. When you ask a question, it automatically retrieves the 2 most relevant code blocks and injects them into its reasoning engine.
*   **Manual Update:** Run `/reindex` whenever you make major changes.

### 🤖 Autonomous Build Loop
The `/build` command triggers a reasoning loop where the agent:
1.  Analyzes your objective.
2.  Writes Python code to perform a step.
3.  Executes the code in the `/workspace` directory.
4.  Inspects the output (and self-heals if it fails).
5.  Repeats until **✅ MISSION COMPLETE**.

### 🎙️ Voice Interface
Send a voice message to The Architect. It uses a local **Whisper** model (optimized for Intel XPU) to transcribe your speech and then processes the text as a standard command or query.

---

## 📂 Project Structure

*   `coder_agent.py`: Main entry point and Telegram loop.
*   `handlers.py`: Logic for all bot commands and message routing.
*   `skill_manager.py`: Manages the sandbox and OpenClaw skill lifecycle.
*   `memory_manager.py`: Neural Memory (RAG) implementation using ChromaDB.
*   `voice_utils.py`: Local Whisper-based voice transcription.
*   `hardware_config.py`: Intel XPU/IPEX initialization logic.
*   `utils.py`: Mobile-optimized formatting and UI utilities.
*   `setup_claw.sh`: Idempotent setup script for MSI Claw environments.
*   `/workspace`: Persistent directory for all autonomous tasks and `/run` commands.
*   `/skills`: Directory for modular, user-approved abilities.

---

## 🔒 Security & Privacy
*   **Local-First:** All inference (Ollama) and transcription (Whisper) happens on your MSI Claw.
*   **Sandbox:** Python code is executed in a subprocess within a dedicated workspace.
*   **Secret Scanning:** Integrated **TruffleHog** scanning via `scripts/pre-push` to prevent accidental token leaks.
*   **Audit Loop:** Every skill installation requires manual SysOp approval and triggers an AI safety audit.

---
*Built for the 90s BBS hacker in all of us. Stay elite.*
