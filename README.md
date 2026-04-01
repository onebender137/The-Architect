# The Architect: Senior Coding Agent for MSI Claw

An elite, local-first coding assistant and OpenClaw skill manager designed specifically for the MSI Claw (Intel Core Ultra 7). Powered by **Qwen 2.5** and **Ollama**.

## 🚀 Features
- **Secure Subprocess Sandbox**: Executes Python code in isolated processes.
- **Self-Healing Loop**: Automatically analyzes runtime errors and generates hotfixes.
- **OpenClaw Skill Manager**: Install, run, and audit modular skills from raw text or GitHub URLs.
- **Secret Management**: Uses `.env` files to keep API tokens off GitHub.

## 🛠️ Setup
1. **Install Ollama**: Ensure Ollama is running and you have pulled the model:
   ```bash
   ollama pull qwen2.5:7b-instruct-q4_0
   ```

2. **Environment Setup**:
   Create a `.env` file in the root directory and add your Telegram token:
   ```text
   BOT_TOKEN=your_token_here
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt python-dotenv
   ```

4. **Run**:
   ```bash
   python coder_agent.py
   ```

## 📂 Project Structure
- `coder_agent.py`: The main brain and Telegram interface.
- `/skills`: Directory where modular OpenClaw skills are installed.
- `.env`: (Hidden/Ignored) Stores your private bot token.
- `.gitignore`: Prevents private files from being pushed to GitHub.
