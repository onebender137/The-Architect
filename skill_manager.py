import os
import re
import shutil
import tempfile
import asyncio
import sys

SKILLS_DIR = os.path.join(os.getcwd(), "skills")
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# ====================== SYSTEM PROMPTS ======================
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

BUILD_LOOP_PROMPT = (
    "You are in an autonomous task execution loop (The Architect /build mode).\n"
    "Your objective is: {goal}\n\n"
    "PREVIOUS ATTEMPT OUTPUT:\n{output}\n\n"
    "State your plan for the next step, then provide the full Python code block to execute.\n"
    "If the task is fully complete and verified, start your response with '✅ MISSION COMPLETE'."
)

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
    """Runs Python code in a persistent workspace directory."""
    temp_file = os.path.join(WORKSPACE_DIR, "task.py")

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            temp_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE_DIR,
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
        return False, f"❌ Workspace Error: {str(e)}"
