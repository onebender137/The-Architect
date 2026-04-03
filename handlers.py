import asyncio
import logging
import re
import subprocess
import os
import base64
from aiogram import types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from skill_manager import SkillManager, run_sandboxed_python, SYSTEM_PROMPT_BASE, SELF_HEAL_PROMPT, BUILD_LOOP_PROMPT
from git_utils import git_manager
from utils import format_output_for_mobile

logger = logging.getLogger(__name__)

def register_handlers(dp, bot, ollama_client, MODEL_NAME, device, user_history, pending_skills, get_context, memory_manager):
    @dp.message(Command("logs"))
    async def cmd_logs(message: types.Message):
        try:
            log_path = "architect.log"
            if not os.path.exists(log_path):
                await message.answer("❌ Log file not found.")
                return

            res = subprocess.run(["tail", "-n", "10", log_path], capture_output=True, text=True)
            output = res.stdout.strip()
            if not output:
                output = "Log is empty."

            await message.answer(format_output_for_mobile(f"📝 **Latest Logs:**\n```text\n{output}\n```"), parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ Failed to read logs: {e}")

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        welcome = (
            "🛠️ **The Architect is Online.**\n\n"
            f"Engine: {MODEL_NAME} ({'Intel Arc Accelerated' if device == 'xpu' else 'CPU Mode'})\n"
            "Security: Python Sandbox + Bash Audit active.\n\n"
            "Use `/help` to see my capabilities."
        )
        await message.answer(format_output_for_mobile(welcome), parse_mode="Markdown")

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        help_text = (
            "🏗️ **Architect Command Menu**\n\n"
            "**/run [code]** — Run Python in secure sandbox\n"
            "**/install_skill [name]** — Add a modular skill\n"
            "**/run_skill [slug]** — Execute a saved skill\n"
            "**/skills** — List all installed skills\n"
            "**/promote [script]** — Move /library script to /skills\n"
            "**/commit [msg]** — Commit & push changes\n"
            "**/scan** — Generate project file tree\n"
            "**/reindex** — Refresh neural memory (RAG)\n"
            "**/build [task]** — Start autonomous build loop\n"
            "**/ingest [file]** — Read file into context\n"
            "**/top** — Monitor real-time system stats\n"
            "**/stats** — Engine & System info\n"
            "**/logs** — View bot runtime logs\n"
            "**/whois** — Display user identification\n"
        )
        await message.answer(format_output_for_mobile(help_text), parse_mode="Markdown")

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        stats_text = (
            "🛠️ **Architect System Stats**\n\n"
            f"**Engine**: `{MODEL_NAME}`\n"
            f"**Device**: `{'Intel Arc XPU' if device == 'xpu' else 'CPU'}`\n"
            f"**Interface**: `Mobile Optimized (50-char)`\n"
            f"**Skills**: `{len(SkillManager.list_skills())} loaded`\n"
            f"**Neural Memory**: `Active` (ChromaDB)\n"
            "**Access**: `SYSOP`"
        )
        await message.answer(format_output_for_mobile(stats_text), parse_mode="Markdown")

    @dp.message(Command("whois"))
    async def cmd_whois(message: types.Message):
        handle = "┬┬Üδ┬│εR"
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
        await message.answer(format_output_for_mobile(box), parse_mode="Markdown")

    @dp.message(Command("top"))
    async def cmd_top(message: types.Message):
        await bot.send_chat_action(message.chat.id, "typing")
        try:
            # Simple top-like output using ps
            # We use a list to avoid shell=True
            res = subprocess.run(
                ["ps", "-eo", "pid,ppid,cmd,%mem,%cpu", "--sort=-%cpu"],
                capture_output=True, text=True, timeout=5
            )
            # Take only the first 10 lines
            output = "\n".join(res.stdout.strip().splitlines()[:10])

            # Also get load average and memory
            load_avg = ""
            if os.path.exists("/proc/loadavg"):
                try:
                    with open("/proc/loadavg", "r") as f:
                        load_avg_vals = f.read().split()[:3]
                    load_avg = f"Load: {' '.join(load_avg_vals)}"
                except Exception:
                    pass

            result = f"📊 **Top Processes:**\n```text\n{output}\n```\n{load_avg}"
            await message.answer(format_output_for_mobile(result), parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ Top failed: {e}")

    @dp.message(Command("scan"))
    async def cmd_scan(message: types.Message):
        await bot.send_chat_action(message.chat.id, "typing")
        try:
            ignore_dirs = [".git", "__pycache__", "venv", ".venv"]
            lines = []
            for root, dirs, files in os.walk("."):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                level = root.replace(".", "", 1).count(os.sep)
                indent = "  " * level
                lines.append(f"{indent}{os.path.basename(root)}/")
                sub_indent = "  " * (level + 1)
                for f in files:
                    lines.append(f"{sub_indent}{f}")

            output = "\n".join(lines)
            summary = f"📂 **Project Structure:**\n```text\n{output}\n```"
            await message.answer(format_output_for_mobile(summary), parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ Scan failed: {e}")

    @dp.message(Command("reindex"))
    async def cmd_reindex(message: types.Message):
        await bot.send_chat_action(message.chat.id, "typing")
        status_msg = await message.answer("🧠 **Neural Memory: Reindexing codebase...**")

        def index_files():
            ignore_dirs = [".git", "__pycache__", "venv", ".venv", "chroma_db"]
            indexed_count = 0
            tasks = []

            for root, dirs, files in os.walk("."):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for f in files:
                    if f.endswith(('.py', '.md', '.sh', '.txt', '.bat', '.json')):
                        filepath = os.path.join(root, f)
                        if os.path.getsize(filepath) < 500000:
                            try:
                                with open(filepath, "r", encoding="utf-8") as file:
                                    content = file.read()
                                    tasks.append((content, {"path": filepath}, filepath))
                            except Exception:
                                continue
            return tasks

        try:
            await memory_manager.clear_memory()
            # Run file collection in a thread to avoid blocking
            indexing_tasks = await asyncio.to_thread(index_files)

            count = 0
            for content, metadata, doc_id in indexing_tasks:
                await memory_manager.add_document(text=content, metadata=metadata, doc_id=doc_id)
                count += 1

            await status_msg.edit_text(format_output_for_mobile(f"✅ **Reindex Complete.**\nIndexed `{count}` files into neural memory."), parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ Reindex failed: {e}")

    @dp.message(Command("ingest"))
    async def cmd_ingest(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("⚠️ Usage: `/ingest [filepath]`")
            return

        filepath = command.args.strip()
        if not os.path.exists(filepath):
            await message.answer(f"❌ File not found: `{filepath}`")
            return

        if os.path.isdir(filepath):
            await message.answer(f"❌ `{filepath}` is a directory. Use `/scan` to see its contents.")
            return

        # 1MB limit for ingest
        size_limit = 1024 * 1024
        if os.path.getsize(filepath) > size_limit:
            await message.answer(f"❌ File is too large (max 1MB).")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            history = get_context(message.from_user.id)
            history.append({'role': 'system', 'content': f"CONTEXT INGESTED: File `{filepath}`:\n---\n{content}\n---"})

            await message.answer(f"✅ Ingested `{filepath}` into conversation context.")
        except Exception as e:
            await message.answer(f"❌ Failed to ingest file: {e}")

    @dp.message(Command("skills"))
    async def cmd_list_skills(message: types.Message):
        skills = SkillManager.list_skills()
        if skills:
            await message.answer(format_output_for_mobile(f"📂 **Installed Skills:**\n" + "\n".join(f"• `{s}`" for s in skills)), parse_mode="Markdown")
        else:
            await message.answer("📂 No skills installed yet.")

    @dp.message(Command("remove_skill"))
    async def cmd_remove_skill(message: types.Message):
        slug = message.text.replace("/remove_skill", "").strip()
        if SkillManager.remove_skill(slug):
            await message.answer(f"🗑️ Skill `{slug}` removed successfully.")
        else:
            await message.answer(f"❌ Skill `{slug}` not found.")

    @dp.message(Command("promote"))
    async def cmd_promote(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("⚠️ Usage: `/promote [script_name]`")
            return

        # Security: Prevent path traversal by only taking the basename
        script_name = os.path.basename(command.args.strip())
        library_path = os.path.abspath(os.path.join("library", script_name))

        # Further security: Ensure the path is still within the library directory
        if not library_path.startswith(os.path.abspath("library")):
            await message.answer("❌ Invalid script name.")
            return

        if not os.path.exists(library_path):
            await message.answer(f"❌ Script `{script_name}` not found in `/library`.")
            return

        # Check if it's a directory with SKILL.md or a single file
        if os.path.isdir(library_path):
            skill_file = os.path.join(library_path, "SKILL.md")
            if not os.path.exists(skill_file):
                await message.answer(f"❌ `{script_name}` is a directory but has no `SKILL.md`.")
                return
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # If it's a file, we wrap it in a bash block as a basic skill
            with open(library_path, "rb") as f:
                file_content_b64 = base64.b64encode(f.read()).decode()

            content = (
                f"# {script_name}\n\n"
                "```bash\n"
                "# Run the script via base64 to avoid delimiter issues\n"
                "TMP_SCRIPT=$(mktemp)\n"
                f"echo '{file_content_b64}' | base64 -d > \"$TMP_SCRIPT\"\n"
                "bash \"$TMP_SCRIPT\"\n"
                "rm \"$TMP_SCRIPT\"\n"
                "```"
            )

        success, result = await SkillManager.install_skill(script_name, content)
        if success:
            await message.answer(f"✅ Promoted `{script_name}` to modular skill: `{result}`.")
        else:
            await message.answer(f"❌ Promotion failed: {result}")

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
            await message.answer(format_output_for_mobile(f"📊 **Result:**\n```text\n{output}\n```"), parse_mode="Markdown")
        except subprocess.TimeoutExpired:
            await message.answer("❌ Skill execution timed out (20s).")
        except Exception as e:
            await message.answer(f"❌ Failed to run skill: {e}")

    @dp.message(Command("build"))
    async def cmd_build(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("🏗️ **Autonomous Build Mode**\nUsage: `/build [task objective]`")
            return

        goal = command.args.strip()
        status_msg = await message.answer(f"🏗️ **The Architect: Starting Autonomous Build Loop...**\nObjective: `{goal}`")

        current_output = "No previous attempts."
        max_iterations = 5

        for i in range(max_iterations):
            await bot.send_chat_action(message.chat.id, "typing")

            prompt = BUILD_LOOP_PROMPT.format(goal=goal, output=current_output)
            messages = [
                {'role': 'system', 'content': SYSTEM_PROMPT_BASE},
                {'role': 'user', 'content': prompt}
            ]

            try:
                res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
                ans = res['message']['content']

                # Check for completion
                if "✅ MISSION COMPLETE" in ans:
                    await message.answer(format_output_for_mobile(f"🏆 **Task Finalized!**\n\n{ans}"), parse_mode="Markdown")
                    break

                # Extract code and execute
                code_match = re.search(r"```python\n(.*?)\n```", ans, re.DOTALL)
                if not code_match:
                    await message.answer(format_output_for_mobile(f"⚠️ **Wait Step:**\n{ans}"), parse_mode="Markdown")
                    break # Break if no code is provided and not finished

                code = code_match.group(1).strip()
                await message.answer(format_output_for_mobile(f"⚙️ **Iteration {i+1}: Executing step...**\n\n{ans}"), parse_mode="Markdown")

                success, output = await run_sandboxed_python(code)
                current_output = output

                if not success:
                    await message.answer(format_output_for_mobile(f"❌ **Step Failed:**\n```text\n{output}\n```"), parse_mode="Markdown")
                else:
                    await message.answer(format_output_for_mobile(f"✅ **Step Result:**\n```text\n{output}\n```"), parse_mode="Markdown")

            except Exception as e:
                await message.answer(f"❌ Build loop error: {e}")
                break
        else:
            await message.answer("🏁 **Max iterations (5) reached. Build loop paused.**")

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
            await message.answer(format_output_for_mobile(f"✅ **Output:**\n```text\n{output}\n```"), parse_mode="Markdown")
        else:
            await message.answer(format_output_for_mobile(f"❌ **Error:**\n```text\n{output}\n```\n\n🔄 **Self-Healing in progress...**"), parse_mode="Markdown")

            history = get_context(message.from_user.id)
            messages = [
                {'role': 'system', 'content': SYSTEM_PROMPT_BASE},
                *list(history),
                {'role': 'user', 'content': SELF_HEAL_PROMPT.format(error=output)}
            ]

            try:
                res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
                await message.answer(format_output_for_mobile(f"🔧 **Suggested Fix:**\n{res['message']['content']}"), parse_mode="Markdown")
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
            format_output_for_mobile(f"🛡️ **Skill Audit Request**\n\nName: `{name}`\n\nInstall this skill?"),
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
            await callback.message.answer(format_output_for_mobile(f"🛡️ **Safety Audit:**\n{audit_text}"), parse_mode="Markdown")
        else:
            await callback.message.edit_text(f"❌ {result}")

    @dp.message(Command("commit"))
    async def cmd_commit(message: types.Message, command: CommandObject):
        commit_msg = command.args or "Update by Jules"

        status_msg = await message.answer(f"🚀 Staging, committing, and pushing: '{commit_msg}'...")

        try:
            result = git_manager("push", commit_msg)
            await status_msg.edit_text(format_output_for_mobile(f"✅ {result}"), parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ Git operation failed: {e}")

    @dp.message(F.text)
    async def handle_text(message: types.Message):
        if not message.text or message.text.startswith('/'):
            return  # Let command handlers take care of commands

        history = get_context(message.from_user.id)
        await bot.send_chat_action(message.chat.id, "typing")

        # RAG: Search neural memory for context
        relevant_context = ""
        memory_results = await memory_manager.search(message.text, n_results=2)
        if memory_results and memory_results['documents']:
            docs = memory_results['documents'][0]
            metas = memory_results['metadatas'][0]
            context_blocks = []
            for i in range(len(docs)):
                path = metas[i].get('path', 'unknown')
                context_blocks.append(f"FILE: {path}\n---\n{docs[i]}\n---")
            relevant_context = "\n\n".join(context_blocks)

        system_prompt = SYSTEM_PROMPT_BASE
        if relevant_context:
            system_prompt += f"\n\nRELEVANT PROJECT CONTEXT:\n{relevant_context}\n"

        messages = [
            {'role': 'system', 'content': system_prompt},
            *list(history),
            {'role': 'user', 'content': message.text}
        ]

        try:
            res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
            ans = res['message']['content']

            # Update history
            history.append({'role': 'user', 'content': message.text})
            history.append({'role': 'assistant', 'content': ans})

            await message.answer(format_output_for_mobile(ans), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            await message.answer("⚠️ Ollama connection error. Make sure `ollama serve` is running.")
