# Welcome to The Architect Wiki

The Architect is an elite, local-first coding assistant and OpenClaw skill manager specifically engineered for the MSI Claw (Intel Core Ultra 7 155H). This wiki provides in-depth documentation on how to optimize, secure, and extend your personal AI mentor.

## 🚀 Key Features

- **Intel Arc Optimized:** Custom Windows-to-WSL bridge ensures the LLM runs on the GPU, not the CPU.
- **Secure Subprocess Sandbox:** Executes generated Python code in isolated temporary directories.
- **OpenClaw Skill Management:** A modular system to install, audit, and run skills via Telegram.
- **Self-Healing Loop:** Automatically monitors execution errors and writes its own hotfixes.
- **Neural Memory (RAG):** Persistent local context from the codebase using ChromaDB and Intel-optimized embeddings.

## 📖 Documentation Sections

### [🏎️ Hardware Tuning](Hardware-Tuning)
Learn how to configure your MSI Claw BIOS, MSI Center M, and environment variables to achieve maximum inference speed (tokens per second) using Intel IPEX.

### [🔒 Security Sandbox Architecture](Security-Sandbox-Architecture)
A technical deep dive into how The Architect safely executes code using isolated temporary directories and subprocess management.

### [🛠️ OpenClaw Skill Management](OpenClaw-Skill-Management)
A comprehensive guide to the modular skill system, including how to install, manage, and run custom skills via Telegram.

### [🧠 Neural Memory (RAG) Architecture](Neural-Memory-RAG)
Technical details on how The Architect stores, retrieves, and utilizes project-wide context using ChromaDB.

---

*The Architect bridges the gap between Windows-based Intel Arc GPU acceleration and Linux-based WSL development, providing a high-performance, low-latency coding mentor that runs entirely on your handheld hardware.*
