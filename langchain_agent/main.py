"""
main.py
Entry point for the CloudOps LangChain Agent.

Memory: each question is sent with the same thread_id so the agent
        accumulates conversation history within a session.
Error handling: all agent and tool errors are caught and shown
                as friendly messages instead of raw tracebacks.
"""

import asyncio
import uuid
from mcp_client import get_tools
from agent import build_agent


async def run():
    print("Starting CloudOps Agent...")
    print("Connecting to MCP server...\n")

    # ── connect to MCP server and get tools ──────────────────────────────
    try:
        tools = await get_tools()
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")
        print("Make sure mcp_entrypoint.py is accessible and all dependencies are installed.")
        return

    print(f"Connected. {len(tools)} tools available:")
    for t in tools:
        print(f"  - {t.name}")
    print()

    # ── build agent ───────────────────────────────────────────────────────
    try:
        agent = build_agent(tools)
    except Exception as e:
        print(f"Failed to build agent: {e}")
        print("Check that GROQ_API_KEY is set correctly in mcp-server/.env")
        return

    # ── session setup ─────────────────────────────────────────────────────
    # thread_id is a unique ID for this session.
    # LangGraph uses it to look up the right conversation history in MemorySaver.
    # Every question in the same run shares the same thread_id → memory works.
    # A new run generates a new thread_id → fresh conversation.
    session_thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_thread_id}}

    print("Ask anything about your AWS infrastructure.")
    print("The agent remembers your conversation within this session.")
    print("Type 'exit' to quit.\n")

    # ── question loop ─────────────────────────────────────────────────────
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            # handle Ctrl+C gracefully
            print("\nExiting...")
            break

        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not question:
            continue

        print()

        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": question}]},
                config=config,   # ← this is what passes thread_id to MemorySaver
            )

            final_message = result["messages"][-1]
            print(f"Agent: {final_message.content}\n")

        except Exception as e:
            # Friendly error messages based on common failure types
            error_str = str(e).lower()

            if "api key" in error_str or "authentication" in error_str or "401" in error_str:
                print("Agent: Authentication failed. Check your GROQ_API_KEY in .env\n")

            elif "rate limit" in error_str or "429" in error_str:
                print("Agent: Rate limit hit on Groq. Wait a few seconds and try again.\n")

            elif "timeout" in error_str or "timed out" in error_str:
                print("Agent: Request timed out. AWS or Groq took too long to respond. Try again.\n")

            elif "aws" in error_str or "botocore" in error_str or "boto3" in error_str:
                print("Agent: AWS returned an error. Check your AWS credentials and permissions in .env\n")

            elif "connection" in error_str or "refused" in error_str:
                print("Agent: Could not connect to a service. Check your internet connection.\n")

            else:
                # For unexpected errors, show a clean message but also the raw error
                # so you can debug it — important during development
                print(f"Agent: Something went wrong. Error: {e}\n")

        print("-" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(run())