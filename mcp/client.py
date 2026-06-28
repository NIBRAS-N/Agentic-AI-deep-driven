"""
MCP Multi-Server Client — LangGraph + Anthropic
================================================

## এই Script কী করে?

দুটো ভিন্ন MCP server-এর tools একসাথে ব্যবহার করে একটা LangGraph agent চালায়:

```
MultiServerMCPClient
  │
  ├── math server  (stdio)  ──► add, subtract, multiply, divide
  └── weather server (http) ──► get_weather
           ↓
    সব tools একসাথে → LangGraph Agent
           ↓
    Human query → Agent → tool call → result → final answer
```

## Architecture

```
Human: "Dhaka-র আবহাওয়া কী? আর (3+5)×12 = কত?"
          ↓
   [call_model] node  ← ChatAnthropic (Claude)
          ↓  (tool_calls আছে)
   tools_condition → [tools] node
          │
          ├── get_weather("dhaka")  → weather MCP server (HTTP)
          └── multiply(add(3,5),12) → math MCP server (stdio)
          ↓
   [call_model] node (আবার) → final answer
          ↓
         END
```

## চালানোর আগে

১. Weather server আলাদা terminal-এ চালু করো:
       uv run python weather.py

২. .env file-এ ANTHROPIC_API_KEY set করো।

৩. তারপর এই client চালাও:
       uv run python client.py

## প্রয়োজনীয় packages

    uv add langchain-mcp-adapters langchain-anthropic langgraph python-dotenv mcp uvicorn
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# Step 1 — Server Paths ও URLs
# ─────────────────────────────────────────────────────────────────
#
# Math server: stdio → absolute path দরকার
#   sys.executable → বর্তমান Python interpreter-এর path (venv সহ)
#   Path(__file__).parent → এই client.py-র directory (= mcp/)
#
# Weather server: HTTP → URL দরকার
#   "/mcp" → FastMCP-এর default streamable-http endpoint path

_MATH_SERVER_PATH = str(Path(__file__).parent / "mathServer.py")
_WEATHER_SERVER_URL = "http://localhost:8000/mcp"


# ─────────────────────────────────────────────────────────────────
# Step 2 — LangGraph Graph তৈরি
# ─────────────────────────────────────────────────────────────────
#
# Graph structure:
#   START → [call_model] ──(tool call আছে?)──► [tools] → [call_model]
#                        └──(নেই)──────────────► END
#
# MessagesState:
#   LangGraph-এর built-in state — শুধু messages list রাখে।
#   add_messages reducer auto-included।

def build_graph(tools: list, llm: ChatAnthropic):
    """MCP tools দিয়ে LangGraph agent graph তৈরি করো।"""

    def call_model(state: MessagesState):
        # প্রতি call-এ tools fresh bind করা হয়
        response = llm.bind_tools(tools).invoke(state["messages"])
        return {"messages": response}

    builder = StateGraph(MessagesState)

    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")

    return builder.compile()


# ─────────────────────────────────────────────────────────────────
# Step 3 — Main: MultiServerMCPClient দিয়ে দুই server connect করো
# ─────────────────────────────────────────────────────────────────

async def main() -> None:
    print("=" * 60)
    print("MCP Multi-Server Client — LangGraph + Anthropic")
    print("=" * 60)

    # ── LLM setup ──────────────────────────────────────────────
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
    print(f"LLM: {llm.model}\n")

    # ── MultiServerMCPClient ────────────────────────────────────
    #
    # MultiServerMCPClient কী করে:
    #   → একাধিক MCP server-এর সাথে সংযোগ manage করে
    #   → প্রতিটা server-এর tools আলাদাভাবে fetch করে
    #   → সব tools একটা list-এ merge করে দেয়
    #   → `async with` block শেষ হলে সব connection বন্ধ করে
    #
    # Connection config:
    #   stdio transport:
    #     "command" → Python executable
    #     "args"    → script path
    #     "transport" → "stdio"
    #
    #   HTTP transport:
    #     "url"       → MCP endpoint URL
    #     "transport" → "streamable_http"

    async with MultiServerMCPClient(
        {
            # ── Math Server (stdio) ───────────────────────────
            # client এই script-কে subprocess হিসেবে চালাবে
            # stdin/stdout দিয়ে JSON-RPC communicate করবে
            "math": {
                "command": sys.executable,
                "args": [_MATH_SERVER_PATH],
                "transport": "stdio",
            },

            # ── Weather Server (streamable-http) ──────────────
            # এই server আগে থেকেই চালু থাকতে হবে:
            #   uv run python weather.py
            "weather": {
                "url": _WEATHER_SERVER_URL,
                "transport": "streamable_http",
            },
        }
    ) as client:

        # ─────────────────────────────────────────────────────
        # Step 4 — Tools Fetch করো
        # ─────────────────────────────────────────────────────
        #
        # get_tools() দুই server-এর সব tools একসাথে return করে:
        #   math server   → [add, subtract, multiply, divide]
        #   weather server → [get_weather]
        #
        # tools list → LangGraph ToolNode-এ পাঠানো হয়

        tools = await client.get_tools()

        print("✓ Connected to MCP servers")
        print(f"✓ Tools loaded: {[t.name for t in tools]}")
        print()

        # ─────────────────────────────────────────────────────
        # Step 5 — Graph তৈরি এবং চালাও
        # ─────────────────────────────────────────────────────

        graph = build_graph(tools, llm)
        print("✓ LangGraph agent ready\n")

        # ── Helper function ───────────────────────────────────
        async def ask(question: str) -> str:
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=question)]}
            )
            return result["messages"][-1].content

        # ── Test 1: Math tool ─────────────────────────────────
        print("─" * 60)
        print("Test 1 — Math Tool (stdio server)")
        print("─" * 60)
        q1 = "What is (3 + 5) × 12? তারপর ফলাফলকে 4 দিয়ে ভাগ করো।"
        print(f"Human: {q1}")
        print(f"AI: {await ask(q1)}")
        print()

        # ── Test 2: Weather tool ──────────────────────────────
        print("─" * 60)
        print("Test 2 — Weather Tool (HTTP server)")
        print("─" * 60)
        q2 = "Dhaka এবং London-এর আবহাওয়া তুলনা করো।"
        print(f"Human: {q2}")
        print(f"AI: {await ask(q2)}")
        print()

        # ── Test 3: দুই server একসাথে ────────────────────────
        print("─" * 60)
        print("Test 3 — Math + Weather একসাথে (multi-server)")
        print("─" * 60)
        q3 = (
            "Tokyo-র আবহাওয়া জানাও এবং বলো "
            "যদি temperature 10 দিয়ে গুণ করা হয় তাহলে কত হয়?"
        )
        print(f"Human: {q3}")
        print(f"AI: {await ask(q3)}")
        print()

        print("=" * 60)
        print("সব test শেষ!")
        print("=" * 60)


# ─────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────
#
# asyncio.run() → async main() function চালায়
# MCP client async/await ব্যবহার করে, তাই async দরকার

if __name__ == "__main__":
    asyncio.run(main())
