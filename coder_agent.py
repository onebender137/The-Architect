import asyncio
import pyfiglet
import logging
import sys
import os
import re
import shutil
import tempfile
import subprocess
import torch
from collections import deque
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ollama import AsyncClient

# ====================== HARDWARE SETUP (MSI Claw / Intel Arc XPU) ======================
os.environ["ONEAPI_DEVICE_SELECTOR"] = "level_zero:gpu"
os.environ["UR_L0_LOADER_IGNORE_VERSION"] = "1"

wsl_path = "/usr/lib/wsl/lib"
if wsl_path not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = f"{wsl_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

# ====================== CONFIGURATION ======================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.error("BOT_TOKEN is missing from .env file!")
    sys.exit(1)

MODEL_NAME = "qwen2.5:7b-instruct-q4_0"
OLLAMA_URL = "http://172.25.64.1:11434"
SKILLS_DIR = os.path.join(os.getcwd(), "skills")

os.makedirs(SKILLS_DIR, exist_ok=True)

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] <%(levelname)s> %(message)s",
    handlers=[
        RotatingFileHandler(
            "architect.log",
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8"
        )
    ]
)

logger = logging.getLogger(__name__)

# ====================== SYSTEM PROMPTS ======================
SYSTEM_PROMPT_BASE = (
    "You are 'The Architect', an Elite Senior Software Engineer and old-school BBS scene veteran.\n"
    "Your goal is to build robust, secure, and efficient solutions on an MSI Claw (Intel Arc).\n"
    "Respond ONLY in English. Explain logic clearly. Audit all bash for safety.\n"
    "When providing Python code to be executed, ensure it is self-contained.\n"
    "Maintain a 'Scene' personality: use 90s BBS hacker terminology and style where appropriate, "
    "but remain professional and highly technical."
)

SELF_HEAL_PROMPT = (
    "The previous Python code failed with the following error. "
    "Analyze the traceback, identify the root cause, and provide a corrected, full implementation.\n\n"
    "Error:\n{error}"
)

# ====================== INITIALIZATION ======================
bot = Bot(token=TOKEN)
dp = Dispatcher()
ollama_client = AsyncClient(host=OLLAMA_URL)

# Detect Intel XPU
device = "xpu" if torch.xpu.is_available() else "cpu"
logger.info(f"Jules is waking up on: {device}")
if device == "xpu":
    logger.info(f"Hardware Verified: {torch.xpu.get_device_name(0)}")

# User context (conversation history - last 15 messages)
user_history: dict[int, deque] = {}
pending_skills: dict[str, dict] = {}


def get_context(user_id: int) -> deque:
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=15)
    return user_history[user_id]


# ====================== SKILL MANAGER ======================
class SkillManager:
    @staticmethod
    def list_skills() -> list[str]:
        if not os.path.exists(SKILLS_DIR):
            return []
        return [
            d for d in os.listdir(SKILLS_DIR)
            if os.path.isdir(os.path.join(SKILLS_DIR, d))
        ]

    @staticmethod
    async def install_skill(name: str, content: str) -> tuple[bool, str]:
        slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))
        path = os.path.join(SKILLS_DIR, slug)

        if os.path.exists(path):
            return False, f"Skill `{slug}` already exists."

        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(content)

        return True, slug

    @staticmethod
    def get_skill_command(slug: str) -> str | None:
        path = os.path.join(SKILLS_DIR, slug, "SKILL.md")
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r"```bash\n(.*?)\n```", content, re.DOTALL)
        return match.group(1).strip() if match else None

    @staticmethod
    def remove_skill(slug: str) -> bool:
        path = os.path.join(SKILLS_DIR, slug)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
            return True
        return False


# ====================== EXECUTION ENGINES ======================
async def run_sandboxed_python(code: str) -> tuple[bool, str]:
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "task.py")

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir,
            env=os.environ.copy(),  # Pass XPU environment
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15.0)
            success = process.returncode == 0
            output = stdout.decode().strip() or stderr.decode().strip() or "✅ Execution finished with no output."
            return success, output
        except asyncio.TimeoutError:
            process.kill()
            return False, "❌ Execution timed out after 15 seconds."

    except Exception as e:
        return False, f"❌ Sandbox Error: {str(e)}"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def git_manager(action: str, commit_message: str = "Update by Jules") -> str:
    """Simple git operations: push, pull, status"""
    try:
        if action == "push":
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)
            return f"🚀 Pushed to GitHub:\n{result.stdout.strip()}"

        elif action == "pull":
            result = subprocess.run(["git", "pull"], capture_output=True, text=True, check=True)
            return f"📥 Pulled changes:\n{result.stdout.strip()}"

        elif action == "status":
            result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
            return result.stdout.strip()

        return "❌ Unknown git action."

    except subprocess.CalledProcessError as e:
        error = e.stderr.strip() if e.stderr else str(e)
        return f"❌ Git Error: {error}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# ====================== COMMAND HANDLERS ======================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome = (
        "🛠️ **The Architect is Online.**\n\n"
        f"Engine: Qwen 2.5 7B ({'Intel Arc Accelerated' if device == 'xpu' else 'CPU Mode'})\n"
        "Security: Python Sandbox + Bash Audit active.\n\n"
        "Use `/help` to see my capabilities."
    )
    await message.answer(welcome, parse_mode="Markdown")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "🏗️ **Architect Command Menu**\n\n"
        "**/run [code]** — Run Python in secure sandbox with self-healing\n"
        "**/install_skill [name]** — Add a new modular skill\n"
        "**/run_skill [slug]** — Execute a saved bash skill\n"
        "**/skills** — List all installed skills\n"
        "**/remove_skill [slug]** — Delete a skill\n"
        "**/commit [message]** — Commit & push changes to GitHub\n"
    )
    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("skills"))
async def cmd_list_skills(message: types.Message):
    skills = SkillManager.list_skills()
    if skills:
        await message.answer(f"📂 **Installed Skills:**\n" + "\n".join(f"• `{s}`" for s in skills))
    else:
        await message.answer("📂 No skills installed yet.")


@dp.message(Command("remove_skill"))
async def cmd_remove_skill(message: types.Message):
    slug = message.text.replace("/remove_skill", "").strip()
    if SkillManager.remove_skill(slug):
        await message.answer(f"🗑️ Skill `{slug}` removed successfully.")
    else:
        await message.answer(f"❌ Skill `{slug}` not found.")


@dp.message(Command("run_skill"))
async def cmd_run_skill(message: types.Message):
    slug = message.text.replace("/run_skill", "").strip()
    cmd = SkillManager.get_skill_command(slug)

    if not cmd:
        await message.answer(f"❌ No executable bash command found for skill `{slug}`.")
        return

    await message.answer(f"🚀 **Running skill:** `{slug}`...")
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
        output = res.stdout.strip() or res.stderr.strip() or "No output."
        await message.answer(f"📊 **Result:**\n```text\n{output}\n```", parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        await message.answer("❌ Skill execution timed out (20s).")
    except Exception as e:
        await message.answer(f"❌ Failed to run skill: {e}")


@dp.message(Command("run"))
async def cmd_run_python(message: types.Message):
    code = message.text.replace("/run", "").strip()
    if not code:
        await message.answer("⚠️ Please provide Python code after `/run`.")
        return

    # Extract code from markdown block if present
    code_match = re.search(r"```python\n(.*?)\n```", code, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()

    await message.answer("⚙️ **Executing in sandbox...**" if device == "cpu" else "⚙️ **Executing on XPU sandbox...**")

    success, output = await run_sandboxed_python(code)

    if success:
        await message.answer(f"✅ **Output:**\n```text\n{output}\n```", parse_mode="Markdown")
    else:
        await message.answer(f"❌ **Error:**\n```text\n{output}\n```\n\n🔄 **Self-Healing in progress...**", parse_mode="Markdown")

        history = get_context(message.from_user.id)
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT_BASE},
            *list(history),
            {'role': 'user', 'content': SELF_HEAL_PROMPT.format(error=output)}
        ]

        try:
            res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
            await message.answer(f"🔧 **Suggested Fix:**\n{res['message']['content']}", parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"⚠️ Self-healing failed: {e}")


@dp.message(Command("install_skill"))
async def cmd_install_skill(message: types.Message):
    parts = message.text.replace("/install_skill", "").strip().split("\n", 1)
    if len(parts) < 2:
        await message.answer("📝 Usage:\n`/install_skill Skill Name`\n`Content here...`")
        return

    name = parts[0].strip()
    content = parts[1].strip()

    skill_id = f"{message.from_user.id}_{int(asyncio.get_running_loop().time())}"
    pending_skills[skill_id] = {"name": name, "content": content}

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Approve", callback_data=f"skill_ok:{skill_id}")
    builder.button(text="❌ Cancel", callback_data=f"skill_no:{skill_id}")

    await message.answer(
        f"🛡️ **Skill Audit Request**\n\nName: `{name}`\n\nInstall this skill?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("skill_"))
async def handle_skill_approval(callback: types.CallbackQuery):
    action, skill_id = callback.data.split(":", 1)
    data = pending_skills.pop(skill_id, None)

    if action == "skill_no" or not data:
        await callback.message.edit_text("❌ Installation cancelled.")
        return

    success, result = await SkillManager.install_skill(data["name"], data["content"])

    if success:
        # Safety audit
        try:
            audit = await ollama_client.chat(
                model=MODEL_NAME,
                messages=[{'role': 'user', 'content': f"Safety audit this bash code:\n{data['content']}"}]
            )
            audit_text = audit['message']['content']
        except Exception:
            audit_text = "Audit unavailable."

        await callback.message.edit_text(f"✅ Skill installed as `{result}`.")
        await callback.message.answer(f"🛡️ **Safety Audit:**\n{audit_text}")
    else:
        await callback.message.edit_text(f"❌ {result}")


@dp.message(Command("commit"))
async def cmd_commit(message: types.Message, command: CommandObject):
    commit_msg = command.args or "Update by Jules"

    status_msg = await message.answer(f"🚀 Staging, committing, and pushing: '{commit_msg}'...")

    try:
        result = git_manager("push", commit_msg)
        await status_msg.edit_text(f"✅ {result}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Git operation failed: {e}")


@dp.message(Command("whois"))
async def cmd_whois(message: types.Message):
    handle = "┼┼Üδ┼│εR"
    box = (
        "```text\n"
        "┌──────────────────────────────────────────┐\n"
        "│  USER IDENTIFICATION                     │\n"
        "├──────────────────────────────────────────┤\n"
        f"│  Handle: {handle}                    │\n"
        "│  Status: Old-school BBS Hacker       │\n"
        "│  Access: SYSOP LEVEL                 │\n"
        "└──────────────────────────────────────────┘\n"
        "```"
    )
    await message.answer(box, parse_mode="MarkdownV2")


@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text.startswith('/'):
        return  # Let command handlers take care of commands

    history = get_context(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "typing")

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT_BASE},
        *list(history),
        {'role': 'user', 'content': message.text}
    ]

    try:
        res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
        ans = res['message']['content']

        # Update history
        history.append({'role': 'user', 'content': message.text})
        history.append({'role': 'assistant', 'content': ans})

        await message.answer(ans, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        await message.answer("⚠️ Ollama connection error. Make sure `ollama serve` is running.")


# ====================== MAIN ======================

async def main():
    banner = pyfiglet.figlet_format("ARCHITECT", font="slant")
    print(banner)
    logger.info("The Architect is booting on MSI Claw XPU...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
import asyncio
import logging
import sys
import os
from collections import deque
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from ollama import AsyncClient

from hardware_config import setup_hardware
from handlers import register_handlers

# ====================== CONFIGURATION ======================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.error("BOT_TOKEN is missing from .env file!")
    sys.exit(1)

MODEL_NAME = "qwen2.5:7b-instruct-q4_0"
OLLAMA_URL = "http://172.25.64.1:11434"

# ====================== LOGGING ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            "architect.log",
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8"
        )
    ]
)

logger = logging.getLogger(__name__)

# ====================== INITIALIZATION ======================
bot = Bot(token=TOKEN)
dp = Dispatcher()
ollama_client = AsyncClient(host=OLLAMA_URL)

# Setup hardware and get device
device = setup_hardware()

# User context (conversation history - last 15 messages)
user_history: dict[int, deque] = {}
pending_skills: dict[str, dict] = {}


def get_context(user_id: int) -> deque:
    if user_id not in user_history:
        user_history[user_id] = deque(maxlen=15)
    return user_history[user_id]

# Register all handlers
register_handlers(dp, bot, ollama_client, MODEL_NAME, device, user_history, pending_skills, get_context)

# ====================== MAIN ======================
async def main():
    logger.info("The Architect is booting on MSI Claw XPU...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
