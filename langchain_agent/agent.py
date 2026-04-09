"""
agent.py
LangChain agent powered by Groq (Llama 3.3 70B).
Uses the new LangChain create_agent API (LangChain 0.3+ / LangGraph based).

Memory: MemorySaver checkpointer keeps full conversation history
        across multiple questions in a single session.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from mcp-server folder
load_dotenv(Path(__file__).parent.parent / "mcp-server" / ".env")

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver


def build_agent(tools):
    """
    Builds and returns a compiled LangGraph agent with memory.

    tools: list of LangChain tools from mcp_client.get_tools()

    Memory works like this:
    - MemorySaver stores all messages (user + agent + tool results)
    - Every ainvoke() call passes a thread_id via config
    - LangGraph uses thread_id to look up and continue the right conversation
    - All previous messages are automatically included in each new LLM call
    """

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

    # MemorySaver stores conversation in RAM for the duration of the session.
    # It is NOT persistent across restarts — each new run starts fresh.
    # For persistent memory across restarts you would use SqliteSaver or PostgresSaver,
    # but MemorySaver is correct for now.
    memory = MemorySaver()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""You are a CloudOps AI assistant. You help users
understand and manage their AWS infrastructure by calling the available tools.

When answering:
- Always call the relevant tool to get real data before answering
- Be concise and clear in your final answer
- If multiple tools are needed, call them in logical order
- Always mention the region when talking about EC2 instances
- Remember what the user has asked before in this conversation and refer to it when relevant""",
        checkpointer=memory,
    )

    return agent