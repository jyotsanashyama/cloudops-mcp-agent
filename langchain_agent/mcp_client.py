"""
mcp_client.py

Connects to the MCP server via stdio and returns all tools
as LangChain-compatible tools using langchain-mcp-adapters.

workflow of this file:
1. find mcp server file "mcp_entrypoint.py"
2. start server as subprocess
3. connects to stdio
4. requests all available tools
5. convert all tools into langchain tools
6. return them to agent

AWS -> Service -> MCP Server -> MCP Client -> Agent -> User
"""

from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVER_PATH = str(
    Path(__file__).parent.parent / "mcp-server" / "mcp_entrypoint.py"
)

MCP_SERVER_DIR = str(
    Path(__file__).parent.parent / "mcp-server"
)

# Create client ONCE at module level — subprocess stays alive for the session
_client = MultiServerMCPClient(
    {
        "cloudops": {
            "command": "python",
            "args": [MCP_SERVER_PATH],
            "transport": "stdio",
            "cwd": MCP_SERVER_DIR,
        }
    }
)

async def get_tools():
    """Get tools from the persistent MCP client."""
    tools = await _client.get_tools()
    return tools