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
from mcp_manager import mcp_manager
from syndicate_manager import syndicate_manager
import json

logger = logging.getLogger(__name__)

def register_handlers(dp, bot, ollama_client, MODEL_NAME, device, user_history, pending_skills, get_context, memory_manager, voice_processor):
    @dp.message(Command("evolve"))
    async def cmd_evolve(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("🧬 **Self-Evolution Protocol**\nUsage: `/evolve [new skill concept]`")
            return

        concept = command.args.strip()
        status_msg = await message.answer(f"🧬 **The Architect: Brainstorming '{concept}'...**")

        evolution_prompt = (
            f"You are evolving your own capabilities. Create a new modular skill for the MSI Claw based on this concept: {concept}\n\n"
            "Requirements:\n"
            "1. Output a full SKILL.md file.\n"
            "2. The skill must use either a ```bash or ```python block for execution.\n"
            "3. If Python, ensure it is self-contained.\n"
            "4. Include a 'Verification' section with a small test script.\n"
            "5. Format the output as: \n"
            "NAME: [Skill Name]\n"
            "CONTENT:\n"
            "[Full SKILL.md content]"
        )

        try:
            res = await ollama_client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': evolution_prompt}])
            ans = res['message']['content']

            name_match = re.search(r"NAME:\s*(.*?)(?:\n|$)", ans, re.IGNORECASE)
            content_match = re.search(r"CONTENT:\s*\n?(.*)", ans, re.DOTALL | re.IGNORECASE)

            if not name_match or not content_match:
                await status_msg.edit_text("❌ Evolution failed: Could not parse LLM output. Please try again.")
                return

            name = name_match.group(1).strip()
            content = content_match.group(1).strip()

            # Trigger the standard installation flow
            skill_id = f"{message.from_user.id}_{int(asyncio.get_running_loop().time())}"
            pending_skills[skill_id] = {"name": name, "content": content}

            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Approve", callback_data=f"skill_ok:{skill_id}")
            builder.button(text="❌ Cancel", callback_data=f"skill_no:{skill_id}")

            await status_msg.edit_text(
                format_output_for_mobile(f"🧬 **Evolution Proposal: {name}**\n\nInstall this new capability?"),
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ Evolution error: {e}")

    @dp.message(Command("mcp_connect"))
    async def cmd_mcp_connect(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("⚠️ Usage: `/mcp_connect [slug] [command] [args...]`")
            return

        parts = command.args.split()
        if len(parts) < 2:
            await message.answer("⚠️ Usage: `/mcp_connect [slug] [command] [args...]`")
            return

        slug = parts[0]
        cmd = parts[1]
        args = parts[2:]

        status_msg = await message.answer(f"🔌 **Connecting to MCP: `{slug}`...**")
        success, result = await mcp_manager.connect_stdio(slug, cmd, args)

        if success:
            await status_msg.edit_text(f"✅ {result}")
        else:
            await status_msg.edit_text(f"❌ Failed to connect: {result}")

    @dp.message(Command("mcp_list"))
    async def cmd_mcp_list(message: types.Message):
        sessions = mcp_manager.list_sessions()
        if not sessions:
            await message.answer("📂 No active MCP sessions.")
            return

        resp = "🔌 **Active MCP Sessions:**\n"
        for s in sessions:
            tools, err = await mcp_manager.list_tools(s)
            if err:
                resp += f"• `{s}` (Error: {err})\n"
            else:
                tool_names = [t.name for t in tools.tools]
                resp += f"• `{s}`: {', '.join(tool_names)}\n"

        await message.answer(format_output_for_mobile(resp), parse_mode="Markdown")

    @dp.message(Command("syndicate"))
    async def cmd_syndicate(message: types.Message):
        syndicate = syndicate_manager.list_syndicate()
        resp = "👥 **The Syndicate (Specialized Sub-Agents):**\n\n"
        for persona in syndicate:
            resp += f"• **{persona.name}**: {persona.description}\n"

        resp += "\nUse `/build_with [agent] [task]` to delegate specialized work."
        await message.answer(format_output_for_mobile(resp), parse_mode="Markdown")

    @dp.message(Command("build_with"))
    async def cmd_build_with(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("🏗️ **Syndicate Build Mode**\nUsage: `/build_with [agent_name] [task objective]`")
            return

        parts = command.args.split(None, 1)
        if len(parts) < 2:
            await message.answer("⚠️ Usage: `/build_with [agent_name] [task objective]`")
            return

        agent_slug = parts[0].capitalize()
        goal = parts[1]

        persona = syndicate_manager.get_persona(agent_slug)
        if not persona:
            await message.answer(f"❌ Agent `{agent_slug}` not found in the Syndicate.")
            return

        status_msg = await message.answer(f"🏗️ **{persona.name} is online...**\nObjective: `{goal}`")

        current_output = "No previous attempts."
        max_iterations = 5

        for i in range(max_iterations):
            await bot.send_chat_action(message.chat.id, "typing")

            # Combine system prompts
            full_system_prompt = f"{SYSTEM_PROMPT_BASE}\n\n{persona.system_prompt}"
            prompt = BUILD_LOOP_PROMPT.format(goal=goal, output=current_output)

            messages = [
                {'role': 'system', 'content': full_system_prompt},
                {'role': 'user', 'content': prompt}
            ]

            try:
                res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
                ans = res['message']['content']

                if "✅ MISSION COMPLETE" in ans:
                    await message.answer(format_output_for_mobile(f"🏆 **{persona.name}: Task Finalized!**\n\n{ans}"), parse_mode="Markdown")
                    break

                code_match = re.search(r"```python\n(.*?)\n```", ans, re.DOTALL)
                if not code_match:
                    await message.answer(format_output_for_mobile(f"⚠️ **{persona.name} Wait Step:**\n{ans}"), parse_mode="Markdown")
                    break

                code = code_match.group(1).strip()
                await message.answer(format_output_for_mobile(f"⚙️ **{persona.name} Iteration {i+1}: Executing...**\n\n{ans}"), parse_mode="Markdown")

                success, output = await run_sandboxed_python(code)
                current_output = output

                if not success:
                    await message.answer(format_output_for_mobile(f"❌ **{persona.name} Error:**\n```text\n{output}\n```"), parse_mode="Markdown")
                else:
                    await message.answer(format_output_for_mobile(f"✅ **{persona.name} Result:**\n```text\n{output}\n```"), parse_mode="Markdown")

            except Exception as e:
                await message.answer(f"❌ Build loop error: {e}")
                break
        else:
            await message.answer(f"🏁 **Max iterations (5) reached. {persona.name} paused.**")

    @dp.message(Command("mcp_call"))
    async def cmd_mcp_call(message: types.Message, command: CommandObject):
        if not command.args:
            await message.answer("⚠️ Usage: `/mcp_call [slug] [tool_name] [json_args]`")
            return

        parts = command.args.split(None, 2)
        if len(parts) < 3:
            await message.answer("⚠️ Usage: `/mcp_call [slug] [tool_name] [json_args]`")
            return

        slug, tool_name, json_args = parts
        try:
            args = json.loads(json_args)
        except json.JSONDecodeError:
            await message.answer("❌ Invalid JSON arguments.")
            return

        status_msg = await message.answer(f"🚀 **Calling `{tool_name}` on `{slug}`...**")
        result, err = await mcp_manager.call_tool(slug, tool_name, args)

        if err:
            await status_msg.edit_text(f"❌ Error: {err}")
        else:
            await status_msg.edit_text(format_output_for_mobile(f"📊 **Result:**\n```json\n{json.dumps(result, indent=2)}\n```"), parse_mode="Markdown")

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
            "**/evolve [concept]** — Brainstorm a new skill\n"
            "**/stats** — Engine & System info\n"
            "**/logs** — View bot runtime logs\n"
            "**/whois** — Display user identification\n"
        )
        await message.answer(format_output_for_mobile(help_text), parse_mode="Markdown")

    @dp.message(Command("hud"))
    async def cmd_hud(message: types.Message):
        await bot.send_chat_action(message.chat.id, "typing")

        try:
            # CPU & Load
            load_avg = "N/A"
            if os.path.exists("/proc/loadavg"):
                with open("/proc/loadavg", "r") as f:
                    load_avg = " ".join(f.read().split()[:3])

            # Memory
            mem_info = "N/A"
            res_mem = subprocess.run(["free", "-m"], capture_output=True, text=True)
            if res_mem.returncode == 0:
                lines = res_mem.stdout.splitlines()
                if len(lines) > 1:
                    parts = lines[1].split()
                    mem_info = f"{parts[2]}MB / {parts[1]}MB"

            # Uptime
            uptime_str = "N/A"
            if os.path.exists("/proc/uptime"):
                with open("/proc/uptime", "r") as f:
                    seconds = float(f.read().split()[0])
                    mins, secs = divmod(seconds, 60)
                    hours, mins = divmod(mins, 60)
                    uptime_str = f"{int(hours)}h {int(mins)}m"

            # GPU (Intel Arc) - Fallback detection
            gpu_status = "ARC [IDLE]"
            if device == "xpu":
                gpu_status = "ARC [ACTIVE]"

            # BBS-Style ASCII HUD
            hud = (
                "```text\n"
                "╔════════════ ARCHITECT HUD ════════════╗\n"
                f"║ CPU LOAD: {load_avg.ljust(27)} ║\n"
                f"║ MEMORY:   {mem_info.ljust(27)} ║\n"
                f"║ UPTIME:   {uptime_str.ljust(27)} ║\n"
                "╟───────────────────────────────────────╢\n"
                f"║ GPU:      {gpu_status.ljust(27)} ║\n"
                f"║ ENGINE:   {MODEL_NAME[:25].ljust(27)} ║\n"
                "╚═══════════════════════════════════════╝\n"
                "```"
            )
            await message.answer(format_output_for_mobile(hud), parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ HUD failed: {e}")

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        stats_text = (
            "🛠️ **Architect System Stats**\n\n"
            f"**Engine**: `{MODEL_NAME}`\n"
            f"**Device**: `{'Intel Arc XPU' if device == 'xpu' else 'CPU'}`\n"
            f"**Interface**: `Mobile Optimized (50-char)`\n"
            f"**Skills**: `{len(SkillManager.list_skills())} loaded`\n"
            f"**Neural Memory**: `Active` (ChromaDB)\n"
            f"**Voice Interface**: `Whisper (Base)`\n"
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
            # If it's a file, we wrap it appropriately
            with open(library_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            if script_name.endswith(".py"):
                content = f"# {script_name}\n\n```python\n{raw_content}\n```"
            else:
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
        result = SkillManager.get_skill_command(slug)

        if not result:
            await message.answer(f"❌ No executable command found for skill `{slug}`.")
            return

        interpreter, cmd = result
        await message.answer(f"🚀 **Running skill:** `{slug}` ({interpreter})...")

        try:
            if interpreter == "bash":
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = res.stdout.strip() or res.stderr.strip() or "No output."
            else:
                # Python execution in sandbox
                success, output = await run_sandboxed_python(cmd)

            await message.answer(format_output_for_mobile(f"📊 **Result:**\n```text\n{output}\n```"), parse_mode="Markdown")
        except subprocess.TimeoutExpired:
            await message.answer("❌ Skill execution timed out (30s).")
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

    @dp.message(F.photo)
    async def handle_photo(message: types.Message):
        await bot.send_chat_action(message.chat.id, "typing")

        photo = message.photo[-1] # Highest resolution
        file_info = await bot.get_file(photo.file_id)

        # Determine VLM model
        vlm_model = os.getenv("VLM_MODEL", "moondream")

        is_vision_audit = message.caption and "/vision_audit" in message.caption

        status_msg = await message.answer(f"👁️ **Analyzing image with `{vlm_model}`...**")

        try:
            # Download photo to memory
            file_buffer = await bot.download_file(file_info.file_path)
            import base64
            img_b64 = base64.b64encode(file_buffer.read()).decode()

            if is_vision_audit:
                prompt = (
                    "Perform a structured 'Vision Audit' on this image. "
                    "Identify hardware components, UI elements, or code snippets. "
                    "Report on potential optimizations, hardware wear, or UI inconsistencies. "
                    "Format as a BBS-style technical report."
                )
            else:
                prompt = message.caption or "Analyze this image for architectural or code-related details."

            res = await ollama_client.generate(
                model=vlm_model,
                prompt=prompt,
                images=[img_b64],
                keep_alive=0
            )
            ans = res['response']

            header = "🛡️ **VISION AUDIT REPORT**" if is_vision_audit else "👁️ **Visual Analysis**"
            await status_msg.edit_text(format_output_for_mobile(f"{header}:\n\n{ans}"), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"VLM error: {e}")
            await status_msg.edit_text(f"❌ Vision Analysis failed: {e}")

    @dp.message(F.voice)
    async def handle_voice(message: types.Message):
        await bot.send_chat_action(message.chat.id, "record_audio")

        voice = message.voice
        file_info = await bot.get_file(voice.file_id)
        file_path = f"temp_voice_{voice.file_id}.ogg"

        await bot.download_file(file_info.file_path, file_path)

        status_msg = await message.answer("🎙️ **Transcribing local voice...**")

        # Transcribe in separate thread to avoid blocking
        transcribed_text = await asyncio.to_thread(voice_processor.transcribe, file_path)

        if os.path.exists(file_path):
            os.remove(file_path)

        if not transcribed_text:
            await status_msg.edit_text("❌ Transcription failed.")
            return

        await status_msg.edit_text(format_output_for_mobile(f"🎙️ **Transcribed:**\n_{transcribed_text}_"), parse_mode="Markdown")

        # Process the transcription as text
        await process_message_text(message, transcribed_text)

    @dp.message(F.text)
    async def handle_text(message: types.Message):
        if not message.text or message.text.startswith('/'):
            return  # Let command handlers take care of commands
        await process_message_text(message, message.text)

    async def process_message_text(message: types.Message, text: str):
        history = get_context(message.from_user.id)

        # Phase 8: Reason Visualizer (Simulation for non-R1 models)
        if "deepseek-r1" in MODEL_NAME.lower():
            status_msg = await message.answer("🧠 **Thinking...**")
        else:
            await bot.send_chat_action(message.chat.id, "typing")

        # RAG: Search neural memory for context
        relevant_context = ""
        memory_results = await memory_manager.search(text, n_results=2)
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
            {'role': 'user', 'content': text}
        ]

        try:
            res = await ollama_client.chat(model=MODEL_NAME, messages=messages)
            ans = res['message']['content']

            # Phase 8: Reason Visualizer Clean-up
            if "deepseek-r1" in MODEL_NAME.lower() and 'status_msg' in locals():
                await status_msg.delete()

            # Update history
            history.append({'role': 'user', 'content': text})
            history.append({'role': 'assistant', 'content': ans})

            await message.answer(format_output_for_mobile(ans), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            await message.answer("⚠️ Ollama connection error. Make sure `ollama serve` is running.")
