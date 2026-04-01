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
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ollama import AsyncClient
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
MODEL_NAME = "qwen2.5:7b-instruct-q4_0" 
OLLAMA_URL = "http://172.25.64.1:11434" 
SKILLS_DIR = os.path.join(os.getcwd(), "skills")

if not os.path.exists(SKILLS_DIR):
    os.makedirs(SKILLS_DIR)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler("architect.log", maxBytes=5000000, backupCount=5)]
)

# --- SYSTEM PROMPTS ---
SYSTEM_PROMPT_BASE = (
    "You are 'The Architect', an Elite Senior Software Engineer.\n"
    "Your goal is to build robust, secure, and efficient solutions on an MSI Claw (Intel Arc).\n"
    "Respond ONLY in English. Explain logic clearly. Audit all bash for safety.\n"
    "When providing Python code to be executed, ensure it is self-contained."
)

SELF_HEAL_PROMPT = (
    "The previous Python code failed with the following error. "
    "Analyze the traceback, identify the root cause, and provide a corrected, full implementation.\n\n"
    "Error:\n{error}"
)

# --- INITIALIZATION ---
if not TOKEN:
    logging.error("BOT_TOKEN missing from .env file!")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = AsyncClient(host=OLLAMA_URL)
user_history = {}
pending_skills = {} # Temporary storage for skills awaiting approval

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
        if os.path.exists(path):
            return False, f"Skill `{slug}` already exists."

        os.makedirs(path, exist_ok=True)
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
    def remove_skill(slug: str):
        path = os.path.join(SKILLS_DIR, slug)
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
        return False

# --- EXECUTION ENGINES ---
async def run_sandboxed_python(code: str):
    """Executes Python code in a temporary directory with a timeout."""
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "task.py")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Execute with 10s timeout
        process = await asyncio.create_subprocess_exec(
            sys.executable, temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
            success = process.returncode == 0
            output = stdout.decode().strip() or stderr.decode().strip() or "✅ Execution finished (no output)."
            return success, output
        except asyncio.TimeoutError:
            process.kill()
            return False, "❌ Execution Timeout (10s limit reached)."

    except Exception as e:
        return False, f"❌ Sandbox Error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# --- COMMAND HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome = (
        "🛠️ **The Architect is Online.**\n\n"
        "Engine: Qwen 2.5 7B (Intel Arc Optimized)\n"
        "Security: Python Sandbox & Bash Audit active.\n\n"
        "Use `/help` to see my capabilities."
    )
    await message.answer(welcome, parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "🏗️ **Architect Command Menu**\n\n"
        "**/run [code]** - Run Python in a secure sandbox with Self-Healing logic.\n"
        "**/install_skill [name] \\n [content/url]** - Add modular skills.\n"
        "**/run_skill [slug]** - Execute a saved bash skill.\n"
        "**/skills** - List all installed capabilities.\n"
        "**/remove_skill [slug]** - Delete a specific skill.\n\n"
        "Simply chat with me to brainstorm or audit code."
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("run"))
async def cmd_run_python(message: types.Message):
    code = message.text.replace("/run", "").strip()
    if not code:
        await message.answer("⚠️ Please provide Python code to run.")
        return

    # Extract code from markdown blocks if present
    code_match = re.search(r"```python\n(.*?)\n```", code, re.DOTALL)
    if code_match: code = code_match.group(1).strip()

    await message.answer("⚙️ **Executing in Sandbox...**")
    success, output = await run_sandboxed_python(code)

    if success:
        await message.answer(f"✅ **Output:**\n```text\n{output}\n```", parse_mode="Markdown")
    else:
        await message.answer(f"❌ **Error Detected:**\n```text\n{output}\n```\n\n🔄 **Starting Self-Healing Loop...**", parse_mode="Markdown")

        # Self-Healing: Feed the error back to the LLM
        history = get_context(message.from_user.id)
        heal_prompt = SELF_HEAL_PROMPT.format(error=output)

        msgs = [{'role': 'system', 'content': SYSTEM_PROMPT_BASE}] + list(history) + [{'role': 'user', 'content': heal_prompt}]
        res = await client.chat(model=MODEL_NAME, messages=msgs)
        fix_suggestion = res['message']['content']

        await message.answer(f"🔧 **Architect's Suggested Fix:**\n{fix_suggestion}", parse_mode="Markdown")

@dp.message(Command("install_skill"))
async def cmd_install(message: types.Message):
    parts = message.text.replace("/install_skill", "").strip().split("\n", 1)
    if len(parts) < 2:
        await message.answer("📝 Usage: `/install_skill Name` \n `URL or Content`")
        return
    
    name, content_input = parts[0].strip(), parts[1].strip()
    await bot.send_chat_action(message.chat.id, "typing")

    # Fetch if it's a URL
    if content_input.startswith("http"):
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(content_input) as r:
                    if r.status == 200:
                        content_input = await r.text()
                    else:
                        raise Exception(f"HTTP Error {r.status}")
        except Exception as e:
            await message.answer(f"❌ Fetch Error: {e}")
            return

    # Store for Interactive Audit
    skill_id = f"{message.from_user.id}_{int(asyncio.get_event_loop().time())}"
    pending_skills[skill_id] = {"name": name, "content": content_input}

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Approve & Install", callback_data=f"skill_ok:{skill_id}")
    builder.button(text="❌ Cancel", callback_data=f"skill_no:{skill_id}")

    preview = content_input[:500] + "..." if len(content_input) > 500 else content_input
    await message.answer(
        f"🛡️ **Interactive Skill Audit**\n\n**Name:** {name}\n**Source Preview:**\n```markdown\n{preview}\n```\n\nInstall this skill to `/skills`?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("skill_"))
async def handle_skill_approval(callback: types.CallbackQuery):
    action, skill_id = callback.data.split(":")
    data = pending_skills.get(skill_id)

    if action == "skill_no" or not data:
        await callback.message.edit_text("❌ Installation cancelled.")
        pending_skills.pop(skill_id, None)
        return

    await callback.message.edit_text("⚙️ Installing and auditing...")
    success, result = await SkillManager.install_skill(data["name"], data["content"])
    
    if success:
        audit_res = await client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': f"Perform a safety audit on this skill code:\n{data['content']}"}])
        await callback.message.answer(f"✅ Skill `{result}` installed.\n\n🛡️ **Security Audit:**\n{audit_res['message']['content']}")
    else:
        await callback.message.answer(f"❌ Error: {result}")

    pending_skills.pop(skill_id, None)

@dp.message(Command("skills"))
async def cmd_list_skills(message: types.Message):
    skills = SkillManager.list_skills()
    if not skills:
        await message.answer("📂 No skills installed.")
    else:
        await message.answer(f"📂 **Installed Skills:**\n- " + "\n- ".join(skills))

@dp.message(Command("remove_skill"))
async def cmd_remove_skill(message: types.Message):
    slug = message.text.replace("/remove_skill", "").strip()
    if SkillManager.remove_skill(slug):
        await message.answer(f"🗑️ Skill `{slug}` removed.")
    else:
        await message.answer(f"❌ Skill `{slug}` not found.")

@dp.message(Command("run_skill"))
async def cmd_run_skill(message: types.Message):
    slug = message.text.replace("/run_skill", "").strip()
    cmd = SkillManager.get_skill_command(slug)
    if not cmd:
        await message.answer(f"❌ No executable bash command found in `{slug}`.")
        return

    await message.answer(f"🚀 **Running Skill `{slug}`...**")
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
        output = res.stdout or res.stderr
        await message.answer(f"📊 **Result:**\n```text\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Execution failed: {str(e)}")

@dp.message(F.text)
async def handle_text(message: types.Message):
    history = get_context(message.from_user.id)
    
    # Check if the user is asking to run code without the /run command
    if "run this" in message.text.lower() and ("```python" in message.text or "import " in message.text):
        await message.answer("💡 *Hint: Use `/run` to execute Python in my secure sandbox.*")

    await bot.send_chat_action(message.chat.id, "typing")
    msgs = [{'role': 'system', 'content': SYSTEM_PROMPT_BASE}] + list(history) + [{'role': 'user', 'content': message.text}]
    
    try:
        res = await client.chat(model=MODEL_NAME, messages=msgs)
        ans = res['message']['content']

        history.append({'role': 'user', 'content': message.text})
        history.append({'role': 'assistant', 'content': ans})

        await message.answer(ans, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ollama Error: {e}")
        await message.answer("⚠️ Connection to local Ollama instance timed out. Check if `ollama serve` is running.")

async def main():
    logging.info("The Architect is booting up...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass