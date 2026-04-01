# 🛠️ OpenClaw Skill Management

The OpenClaw Skill Manager is a modular, extensible system for adding and managing custom capabilities for The Architect. This guide details how to install, audit, and use your skills via the Telegram interface.

---

## 📂 Skill System Structure

Each skill is stored in its own directory within the `skills/` folder. A skill's core logic is defined in a `SKILL.md` file, which includes:
- **Description:** A brief overview of what the skill does.
- **Bash Block:** The actual command or script that The Architect will execute.

### 🧠 Dynamic Prompt Injection

When you interact with The Architect, it dynamically scans the `/skills` directory to understand its current capabilities. The `SkillManager.get_skills_summary()` function generates a real-time summary of all installed skills, which is then injected into the LLM's system prompt.

---

## 🚀 Telegram User Guide

The Architect's skills can be managed using the following Telegram commands:

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/skills` | `/skills` | Lists all currently installed skills and their descriptions. |
| `/install_skill` | `/install_skill Name \n Content/URL` | Installs a new skill. You can provide the raw content or a URL to a `SKILL.md` file. |
| `/run_skill` | `/run_skill [slug]` | Executes the bash command block defined within the specified skill's `SKILL.md`. |
| `/remove_skill` | `/remove_skill [slug]` | Deletes the skill and its directory from the `skills/` folder. |
| `/scan` | `/scan` | Maps the current project files so the LLM is aware of the codebase structure. |
| `/ingest` | `/ingest [file]` | Reads the content of a specific file into the LLM's context. |
| `/run` | `/run [code]` | Executes a Python script in the [Security Sandbox](Security-Sandbox-Architecture). |

### 🛡️ Senior Tip: Safety Audit

Whenever you use `/install_skill`, The Architect automatically performs an **LLM-driven Safety Audit** before saving the skill to your device. This ensures that any third-party scripts or URLs you provide are free of destructive commands or security risks.

---

## 🛠️ Writing Your Own Skill

To create a compatible skill, your `SKILL.md` should follow this structure:

```markdown
# Skill Name

## Description
A brief description of what this skill does for the AI's awareness.

## Implementation
```bash
# The actual command to be executed
python3 scripts/my_custom_tool.py --flag
```
```
