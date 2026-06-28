"""
MCP Weather Server — Streamable-HTTP Transport
===============================================

## stdio বনাম streamable-http

| Feature        | stdio (mathServer.py)          | streamable-http (এই file)         |
|----------------|--------------------------------|-----------------------------------|
| চালানোর পদ্ধতি | client স্বয়ংক্রিয়ভাবে spawn করে | আলাদাভাবে আগেই চালু রাখতে হয়     |
| যোগাযোগ        | stdin / stdout                 | HTTP POST to /mcp endpoint        |
| Use case       | local tools, সহজ setup         | network-accessible, production    |
| Port           | কোনো port লাগে না              | 8000 (বা যেকোনো port)            |

## কীভাবে কাজ করে

```
Client
  │
  ├── HTTP POST → http://localhost:8000/mcp
  │                     ↓
  │               MCP Server (এই script)
  │               → get_weather("dhaka") চালায়
  │               → result return করে
  └── HTTP Response ← JSON result
```

## Tool

| Tool        | কাজ                           | Input       | Output |
|-------------|-------------------------------|-------------|--------|
| get_weather | শহরের আবহাওয়া জানাও           | city: str   | str    |

## চালানোর নিয়ম

client.py চালানোর আগে এই server চালু রাখতে হবে:

    uv run python weather.py

তারপর client HTTP দিয়ে connect করবে:
    http://localhost:8000/mcp

## প্রয়োজনীয় package

    uv add mcp uvicorn
"""

from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────────────────────────
# Step 1 — FastMCP Server তৈরি
# ─────────────────────────────────────────────────────────────────
#
# host এবং port constructor-এ দেওয়া যায় অথবা mcp.run()-এ।
# Streamable-HTTP endpoint: http://<host>:<port>/mcp

mcp = FastMCP("Weather Server", host="localhost", port=8000)


# ─────────────────────────────────────────────────────────────────
# Step 2 — Sample Weather Database
# ─────────────────────────────────────────────────────────────────
#
# Real application-এ এখানে actual weather API call হতো
# (যেমন OpenWeatherMap, WeatherAPI ইত্যাদি)।
# শেখার উদ্দেশ্যে static data ব্যবহার করা হচ্ছে।

_WEATHER_DB: dict[str, dict[str, str]] = {
    "dhaka": {
        "temperature": "34°C",
        "condition":   "Sunny",
        "humidity":    "72%",
        "wind_speed":  "10 km/h",
        "feels_like":  "38°C",
    },
    "chittagong": {
        "temperature": "32°C",
        "condition":   "Partly Cloudy",
        "humidity":    "78%",
        "wind_speed":  "14 km/h",
        "feels_like":  "36°C",
    },
    "london": {
        "temperature": "17°C",
        "condition":   "Overcast",
        "humidity":    "85%",
        "wind_speed":  "20 km/h",
        "feels_like":  "15°C",
    },
    "new york": {
        "temperature": "22°C",
        "condition":   "Clear",
        "humidity":    "55%",
        "wind_speed":  "15 km/h",
        "feels_like":  "21°C",
    },
    "tokyo": {
        "temperature": "28°C",
        "condition":   "Partly Cloudy",
        "humidity":    "65%",
        "wind_speed":  "12 km/h",
        "feels_like":  "30°C",
    },
}


# ─────────────────────────────────────────────────────────────────
# Step 3 — Tool Register করো
# ─────────────────────────────────────────────────────────────────

@mcp.tool()
def get_weather(city: str) -> str:
    """
    যেকোনো শহরের বর্তমান আবহাওয়া জানাও।
    Available cities: dhaka, chittagong, london, new york, tokyo.
    """
    key = city.lower().strip()

    if key not in _WEATHER_DB:
        available = ", ".join(_WEATHER_DB.keys())
        return (
            f"'{city}'-র আবহাওয়া data পাওয়া যায়নি। "
            f"Available cities: {available}"
        )

    w = _WEATHER_DB[key]
    return (
        f"Weather in {city.title()}:\n"
        f"  Temperature : {w['temperature']} (feels like {w['feels_like']})\n"
        f"  Condition   : {w['condition']}\n"
        f"  Humidity    : {w['humidity']}\n"
        f"  Wind Speed  : {w['wind_speed']}"
    )


# ─────────────────────────────────────────────────────────────────
# Step 4 — Server চালু করো (streamable-http)
# ─────────────────────────────────────────────────────────────────
#
# transport="streamable-http":
#   → HTTP server চালু হবে (uvicorn দরকার)
#   → Endpoint: http://localhost:8000/mcp
#   → Client HTTP POST দিয়ে communicate করবে
#
# এই server চালু থাকা অবস্থায় client.py চালাতে হবে।

if __name__ == "__main__":
    print("Weather MCP Server চালু হচ্ছে...")
    print("Endpoint: http://localhost:8000/mcp")
    print("বন্ধ করতে Ctrl+C চাপো।")
    mcp.run(transport="streamable-http")
