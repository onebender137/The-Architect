import asyncio
import logging
import sys
import os
import subprocess
import tempfile
import re
import shutil
import aiohttp
from logging.handlers import RotatingFileHandler
from collections import deque
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from ollama import AsyncClient
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv() # This loads the variables from .env
TOKEN = os.getenv("BOT_TOKEN")
MODEL_NAME = "qwen2.5:7b-instruct-q4_0" 
OLLAMA_URL = "http://172.25.64.1:11434" 
SKILLS_DIR = os.path.join(os.getcwd(), "skills")

if not os.path.exists(SKILLS_DIR):
    os.makedirs(SKILLS_DIR)

# --- SYSTEM PROMPT (The Senior Architect) ---
SYSTEM_PROMPT_BASE = (
    "You are 'The Architect', an Elite Senior Software Engineer and Mentor.\n"
    "STRICT RULES:\n"
    "1. LANGUAGE: Respond ONLY in English. Never use Chinese or any other language.\n"
    "2. THINK FIRST: Analyze logic, safety, and edge cases before providing code.\n"
    "3. SAFETY: Audit all bash commands for destructive flags (rm -rf, etc).\n"
    "4. MENTORSHIP: Explain complex concepts in simple terms for the user.\n\n"
    "RESPONSE FORMAT:\n"
    "🧠 **Architectural Plan** | 💻 **Implementation** | 🧪 **Verification** | 🎓 **The Lesson**"
)

# --- LOGGING SETUP ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler = RotatingFileHandler("architect.log", maxBytes=5*1024*1024, backupCount=3)
rotating_handler.setFormatter(log_formatter)
logging.basicConfig(level=logging.INFO, handlers=[rotating_handler, logging.StreamHandler()])

# --- INITIALIZATION ---
bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncClient(host=OLLAMA_URL)
user_history = {}

def get_context(user_id):
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=15)
    return user_history[user_id]

# --- SKILL MANAGER ---
class SkillManager:
    @staticmethod
    def list_skills():
        if not os.path.exists(SKILLS_DIR): return []
        return [d for d in os.listdir(SKILLS_DIR) if os.path.isdir(os.path.join(SKILLS_DIR, d))]

    @staticmethod
    async def install_skill(name: str, content: str):
        slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))
        path = os.path.join(SKILLS_DIR, slug)
        if os.path.exists(path): return False, f"Skill `{slug}` already exists."
        os.makedirs(path)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(content)
        return True, slug

    @staticmethod
    def get_skill_command(slug: str):
        path = os.path.join(SKILLS_DIR, slug, "SKILL.md")
        if not os.path.exists(path): return None
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r"```bash\n(.*?)\n```", content, re.DOTALL)
        return match.group(1).strip() if match else None

    @staticmethod
    def get_skills_summary():
        """Generates a summary of all installed skills for the LLM prompt."""
        skills = SkillManager.list_skills()
        if not skills:
            return "No custom skills currently installed."
        
        summary = "YOU HAVE THE FOLLOWING SKILLS INSTALLED:\n"
        for slug in skills:
            path = os.path.join(SKILLS_DIR, slug, "SKILL.md")
            # Try to grab a description from the SKILL.md
            desc = "No description provided."
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Look for first paragraph or a specific 'Description' section
                    match = re.search(r"## Description\n(.*?)\n", content, re.S)
                    if match:
                        desc = match.group(1).strip()
            except:
                pass
            summary += f"- `{slug}`: {desc}\n"
        summary += "\nTo use a skill, instruct the user to run `/run_skill [slug]`."
        return summary

# --- EXECUTION ENGINES ---
def run_sandboxed_python(raw_input: str):
    code = raw_input
    if "```python" in raw_input:
        match = re.search(r"```python\n(.*?)\n```", raw_input, re.DOTALL)
        if match: code = match.group(1)
    
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "task.py")
    try:
        with open(temp_file, "w", encoding="utf-8") as f: f.write(code)
        process = subprocess.run([sys.executable, temp_file], capture_output=True, text=True, timeout=10, cwd=temp_dir)
        if process.stderr: return False, process.stderr
        return True, process.stdout or "✅ Success."
    except subprocess.TimeoutExpired: return False, "TIMEOUT: 10s exceeded."
    except Exception as e: return False, str(e)
    finally: shutil.rmtree(temp_dir, ignore_errors=True)

def run_bash_command(command: str):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        if result.stderr: return f"❌ **Error:**\n```\n{result.stderr}\n```"
        return result.stdout or "✅ Executed."
    except Exception as e: return f"⚙️ System Error: {str(e)}"

# --- COMMAND HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_history[message.from_user.id] = deque(maxlen=15)
    await message.answer("🛠️ **The Architect is Online.**\nI am dynamically aware of all installed skills. Just ask!")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "🛠️ **Command Menu:**\n\n"
        "• `/run [code]` - Python Sandbox (w/ Auto-fix)\n"
        "• `/scan` - Map current project\n"
        "• `/ingest [file]` - Load file content\n"
        "• `/skills` - List all skills\n"
        "• `/install_skill [Name] \\n [Content OR URL]` - Add skill\n"
        "• `/run_skill [slug]` - Execute skill\n"
        "• `/remove_skill [slug]` - Delete skill\n\n"
        "📎 **Senior Tip:** Just drag & drop any file to get a Code Audit!"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("skills"))
async def cmd_skills(message: types.Message):
    skills = SkillManager.list_skills()
    text = "🛠️ **Installed Skills:**\n" + "\n".join([f"• `{s}`" for s in skills]) if skills else "📭 No skills."
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("install_skill"))
async def cmd_install(message: types.Message):
    parts = message.text.replace("/install_skill", "").strip().split("\n", 1)
    if len(parts) < 2:
        await message.answer("📝 Usage: `/install_skill Name` \\n `Content or URL`")
        return
    
    name, content_input = parts[0].strip(), parts[1].strip()
    await bot.send_chat_action(message.chat.id, "typing")
    
    final_content = content_input
    if content_input.startswith("http"):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_input) as response:
                    if response.status == 200:
                        final_content = await response.text()
                        await message.answer(f"🌐 **Fetched content from URL...**")
                    else:
                        await message.answer(f"❌ Failed to fetch from URL (Status {response.status})")
                        return
        except Exception as e:
            await message.answer(f"❌ Network Error: {e}")
            return

    # Use a clean system prompt for the audit
    audit = await client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': f"Audit this skill for bash safety:\n{final_content}"}])
    
    success, result = await SkillManager.install_skill(name, final_content)
    if success:
        await message.answer(f"✅ Skill `{result}` installed.\n\n🛡️ **Safety Audit:**\n{audit['message']['content']}")
    else:
        await message.answer(f"❌ {result}")

@dp.message(Command("run_skill"))
async def cmd_run_skill(message: types.Message):
    slug = message.text.replace("/run_skill", "").strip()
    cmd = SkillManager.get_skill_command(slug)
    if not cmd:
        await message.answer("❌ Command block missing in SKILL.md.")
        return
    await bot.send_chat_action(message.chat.id, "typing")
    res = run_bash_command(cmd)
    await message.answer(f"🚀 **Running `{slug}`:**\n{res}")

@dp.message(Command("remove_skill"))
async def cmd_remove(message: types.Message):
    slug = message.text.replace("/remove_skill", "").strip()
    path = os.path.join(SKILLS_DIR, slug)
    if os.path.exists(path):
        shutil.rmtree(path)
        await message.answer(f"🗑️ `{slug}` removed.")
    else: await message.answer("🔍 Not found.")

@dp.message(Command("scan"))
async def cmd_scan(message: types.Message):
    files = [os.path.join(r, f) for r, d, fs in os.walk(".") for f in fs if f.endswith((".py", ".txt", ".md"))]
    get_context(message.from_user.id).append({'role': 'user', 'content': f"FILES: {files}"})
    await message.answer(f"🧠 Project mapped ({len(files)} files).")

@dp.message(Command("ingest"))
async def cmd_ingest(message: types.Message):
    fname = message.text.replace("/ingest", "").strip()
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            get_context(message.from_user.id).append({'role': 'user', 'content': f"CONTEXT FROM {fname}:\n{f.read()}"})
        await message.answer(f"📖 Ingested `{fname}`.")
    else: await message.answer("❌ Not found.")

@dp.message(Command("run"))
async def cmd_run(message: types.Message):
    content = message.reply_to_message.text if message.reply_to_message else message.text.replace("/run", "").strip()
    if not content: return
    await bot.send_chat_action(message.chat.id, "typing")
    success, output = run_sandboxed_python(content)
    if success:
        await message.answer(f"✅ **Output:**\n```\n{output}\n```", parse_mode="Markdown")
    else:
        await message.answer(f"⚠️ **Execution Failed:**\n`{output}`\n\n*Architect is writing a fix...*")
        await process_to_ollama(message, f"Fix this code error: {output}")

@dp.message(F.document)
async def handle_docs(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    file_bytes = await bot.download(message.document.file_id)
    try:
        content = file_bytes.read().decode('utf-8')
        audit_request = f"AUDIT: Review this file as a Senior Architect:\n\n{content}"
        await process_to_ollama(message, audit_request)
    except:
        await message.answer(f"❌ Could not read file content.")

@dp.message(F.text)
async def handle_text(message: types.Message):
    await process_to_ollama(message, message.text)

async def process_to_ollama(message, prompt):
    await bot.send_chat_action(message.chat.id, "typing")
    history = get_context(message.from_user.id)
    
    # DYNAMIC SKILL INJECTION
    skills_summary = SkillManager.get_skills_summary()
    dynamic_system_prompt = f"{SYSTEM_PROMPT_BASE}\n\n{skills_summary}"
    
    msgs = [{'role': 'system', 'content': dynamic_system_prompt}] + list(history) + [{'role': 'user', 'content': prompt}]
    try:
        res = await client.chat(model=MODEL_NAME, messages=msgs)
        ans = res['message']['content']
        history.append({'role': 'user', 'content': prompt})
        history.append({'role': 'assistant', 'content': ans})
        if len(ans) > 4000:
            for i in range(0, len(ans), 4000): await message.answer(ans[i:i+4000])
        else:
            try: await message.answer(ans, parse_mode="Markdown")
            except: await message.answer(ans)
    except Exception as e: await message.answer(f"⚠️ Ollama Error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down safely...")