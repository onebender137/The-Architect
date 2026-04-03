import asyncio
import logging
import re
import subprocess
from aiogram import types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from skill_manager import SkillManager, run_sandboxed_python, SYSTEM_PROMPT_BASE, SELF_HEAL_PROMPT
from git_utils import git_manager

logger = logging.getLogger(__name__)

def register_handlers(dp, bot, ollama_client, MODEL_NAME, device, user_history, pending_skills, get_context):
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        welcome = (
            "🛠️ **The Architect is Online.**\n\n"
            f"Engine: {MODEL_NAME} ({'Intel Arc Accelerated' if device == 'xpu' else 'CPU Mode'})\n"
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
