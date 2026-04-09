"""
core/agent_manager.py
Manages the LangChain agent and MCP tools as a singleton.
Initialised ONCE when the FastAPI server starts.
All chat requests reuse the same agent instance — no subprocess
spawned per request, memory works across requests via thread_id.
"""

import sys
from pathlib import Path

# Add langchain_agent folder to path so we can import from it
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "langchain_agent"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp-server"))

from mcp_client import get_tools
from agent import build_agent


class AgentManager:
    """
    Holds the agent and tools after initialisation.
    Used as app.state.agent_manager in FastAPI.
    """

    # setup empty defaults to use later 
    def __init__(self):
        self.agent = None
        self.tools = []
        self.ready = False

    async def initialise(self):
        """
        Called once on server startup via FastAPI lifespan.
        Connects to MCP server and builds the agent.
        """
        print("Initialising MCP connection and agent...")
        
        self.tools = await get_tools()   # spaws mcp subprocess, gets 5 tools
        self.agent = build_agent(self.tools)  # create Groq llm + agent with memory
        self.ready = True                      # now ready to handle requests
        
        print(f"Agent ready with {len(self.tools)} tools.")

    # called on every /chat requests
    async def chat(self, message: str, thread_id: str) -> str:
        """
        Run the agent with a message and thread_id.
        thread_id links to MemorySaver so conversation history
        is preserved across multiple calls with the same thread_id.
        Returns the agent's final answer as a string.
        """
        if not self.ready:
            raise RuntimeError("Agent not initialised yet")

        config = {"configurable": {"thread_id": thread_id}}

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,  # thread_id tells MemorySaver which convo to continue 
        )

        final_message = result["messages"][-1]
        return final_message.content