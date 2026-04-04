# 🔌 MCP Bridge Architecture

The Architect implements a bridge to the **Model Context Protocol (MCP)**, allowing for standardized integration with external tools and services.

## 🔌 Connection via Stdio

The Architect uses the `stdio` transport to communicate with MCP servers. This allows it to call tools from any MCP-compliant server (e.g., Brave Search, GitHub, Google Drive).

### 🕹️ Commands

| Command | Description |
| :--- | :--- |
| `/mcp_connect [slug] [cmd]` | Connect to an MCP server via stdio. |
| `/mcp_list` | List active sessions and their tools. |
| `/mcp_call [slug] [tool] [json]` | Execute a tool with JSON arguments. |

## 🛠️ Implementation

The `mcp_manager.py` module handles the lifecycle of MCP sessions. It uses the `mcp` Python library to manage the client sessions and transport.

### 🛡️ Security
MCP servers are executed as separate processes, providing a layer of isolation from the main Architect bot.
