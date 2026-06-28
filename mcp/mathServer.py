"""
MCP Math Server — stdio Transport
==================================

## এই Server কী?

MCP (Model Context Protocol) হলো Anthropic-এর তৈরি একটা open protocol যেটা
AI model-কে external tools/data-এর সাথে সংযুক্ত করে।

এই server stdio transport ব্যবহার করে — মানে client এই script-কে
একটা **subprocess** হিসেবে spawn করে এবং stdin/stdout দিয়ে communicate করে।

```
Client
  │
  ├── subprocess spawn করে: python mathServer.py
  │
  ├── stdin  ──►  MCP request (JSON)   ──►  Server
  └── stdout ◄──  MCP response (JSON)  ◄──  Server
```

## Tools

| Tool       | কাজ                    | Input      | Output  |
|------------|------------------------|------------|---------|
| add        | a + b                  | a, b: float | float  |
| subtract   | a - b                  | a, b: float | float  |
| multiply   | a × b                  | a, b: float | float  |
| divide     | a ÷ b                  | a, b: float | float  |

## চালানোর নিয়ম

এই server সরাসরি চালানো যায় (test করতে):
    uv run python mathServer.py

কিন্তু সাধারণত client.py স্বয়ংক্রিয়ভাবে এটাকে spawn করে।

## প্রয়োজনীয় package

    uv add mcp
"""

from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────────────────────────
# Step 1 — FastMCP Server তৈরি
# ─────────────────────────────────────────────────────────────────
#
# FastMCP = MCP server বানানোর সহজ wrapper।
#
# FastMCP vs raw MCP Server:
#   raw MCP Server → boilerplate বেশি, low-level
#   FastMCP        → decorator দিয়ে সহজে tool/resource register করা যায়
#
# "Math Server" → server-এর নাম (client inspect করতে পারে)

mcp = FastMCP("Math Server")


# ─────────────────────────────────────────────────────────────────
# Step 2 — Tools Register করো
# ─────────────────────────────────────────────────────────────────
#
# @mcp.tool() decorator:
#   ✅ Function-কে MCP tool হিসেবে register করে
#   ✅ Docstring → tool description হয় (LLM এটা পড়ে কখন call করবে বোঝে)
#   ✅ Type hints → input/output JSON schema হয়
#   ✅ Return value → LLM-কে tool result হিসেবে পাঠানো হয়
#
# LLM যখন tool call করে, তখন এই ক্রম অনুসরণ হয়:
#
#   LLM → tool_calls: [{name: "add", args: {a: 3, b: 5}}]
#       ↓
#   MCP Server → add(a=3, b=5) → 8
#       ↓
#   LLM → ToolMessage: "8" দেখে final answer তৈরি করে


@mcp.tool()
def add(a: float, b: float) -> float:
    """দুটো সংখ্যা যোগ করো। (Add two numbers: returns a + b)"""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """a থেকে b বিয়োগ করো। (Subtract b from a: returns a - b)"""
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """দুটো সংখ্যা গুণ করো। (Multiply two numbers: returns a × b)"""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """
    a-কে b দিয়ে ভাগ করো। (Divide a by b: returns a ÷ b)
    সতর্কতা: b শূন্য হলে error দেবে।
    """
    if b == 0:
        raise ValueError("শূন্য দিয়ে ভাগ করা যায় না (division by zero is undefined)")
    return a / b


# ─────────────────────────────────────────────────────────────────
# Step 3 — Server চালু করো
# ─────────────────────────────────────────────────────────────────
#
# transport="stdio":
#   → stdin থেকে JSON-RPC request পড়বে
#   → stdout-এ JSON-RPC response লিখবে
#   → Client এই process-কে subprocess হিসেবে চালাবে
#
# অন্য transport options:
#   "streamable-http" → HTTP endpoint (weather.py-তে দেখো)
#   "sse"             → Server-Sent Events

if __name__ == "__main__":
    print("Math MCP Server চালু হচ্ছে (stdio transport)...", flush=True)
    mcp.run(transport="stdio")
