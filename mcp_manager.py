import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPManager:
    def __init__(self):
        self.sessions = {} # {slug: session}
        self.server_params = {} # {slug: StdioServerParameters}

    async def connect_stdio(self, slug: str, command: str, args: list[str] = None, env: dict = None):
        """Connects to an MCP server via stdio."""
        if slug in self.sessions:
            return False, f"Session '{slug}' already exists."

        params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env
        )

        try:
            # Note: We need to manage the context managers properly
            # This is a bit tricky for a persistent manager
            transport_ctx = stdio_client(params)
            read, write = await transport_ctx.__aenter__()
            session = ClientSession(read, write)
            await session.initialize()

            self.sessions[slug] = (session, transport_ctx)
            self.server_params[slug] = params
            return True, f"Connected to MCP server '{slug}' via stdio."
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {slug}: {e}")
            return False, str(e)

    async def list_tools(self, slug: str):
        if slug not in self.sessions:
            return None, f"No session found for '{slug}'."

        session, _ = self.sessions[slug]
        try:
            tools = await session.list_tools()
            return tools, None
        except Exception as e:
            return None, str(e)

    async def call_tool(self, slug: str, tool_name: str, arguments: dict):
        if slug not in self.sessions:
            return None, f"No session found for '{slug}'."

        session, _ = self.sessions[slug]
        try:
            result = await session.call_tool(tool_name, arguments)
            return result, None
        except Exception as e:
            return None, str(e)

    async def disconnect(self, slug: str):
        if slug in self.sessions:
            session, transport_ctx = self.sessions.pop(slug)
            await transport_ctx.__aexit__(None, None, None)
            self.server_params.pop(slug, None)
            return True
        return False

    def list_sessions(self):
        return list(self.sessions.keys())

mcp_manager = MCPManager()
