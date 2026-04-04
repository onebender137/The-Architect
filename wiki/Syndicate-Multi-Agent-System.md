# 👥 The Syndicate & Multi-Agent System

The Architect utilize a specialized multi-agent architecture known as **The Syndicate**. This system allows the primary agent to delegate complex tasks to specialized personas with unique system prompts and expertise.

## 👥 Syndicate Personas

| Persona | Role | Specialization |
| :--- | :--- | :--- |
| **Ghost** | Security | Secret scanning, code audits, compliance. |
| **Pulse** | Performance | Intel Arc/XPU optimization, IPEX tuning. |
| **Spark** | UI/UX | Mobile-optimized interfaces and dashboards. |
| **Specter** | Red Team | Penetration testing and exploit discovery. |

## 🛠️ Usage

To delegate a task to a specific Syndicate member, use the `/build_with` command:

```text
/build_with [persona] [task objective]
```

Example:
`/build_with Ghost audit the current sandbox for directory traversal vulnerabilities`

## 🧠 Autonomous Loop
Syndicate members operate within the same **Autonomous Build Loop** as the primary Architect, meaning they can write, execute, and self-heal code to achieve their objectives.
