"""A tool server (MCP) with the three tools of custom_tools_agent.py, as its own program (Lesson 6, Part 2).

WHAT
    Offers the tools convert_units, weekday and add_business_days to any MCP client: claude -p, the
    interactive claude window, Claude Desktop. They call the same functions as the converting-units
    and calculating-dates skills.

WHY
    The claude -p way of custom_tools_agent.py (--cli) can't reach functions inside a Python program,
    so the tools must be served by a separate program that Claude Code starts. This file is that
    program. It also shows what MCP really is: JSON messages, one per line.

HOW IT WORKS
    Claude Code starts the program, and talks to it over stdin and stdout, one JSON-RPC message per
    line. handle() answers each request:
        initialize   ->  the protocol version, "I have tools", and the server's name
        tools/list   ->  each tool's name, description and inputSchema (JSON Schema of its parameters)
        tools/call   ->  runs one tool with Claude's arguments; the result is JSON text, and
                         "isError": true if the function reported an error
    Messages without an "id" are notifications (for example notifications/initialized): no answer.
    stdout carries only these messages, so the program never prints anything else.

HOW TO USE IT
    custom_tools_agent.py --cli starts it through --mcp-config. To use the tools in the interactive
    claude window too, register it once (from the project folder, with the venv activated):
        claude mcp add tutor -- python agent/tutor_mcp_server.py
    and remove it again with:  claude mcp remove tutor

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude. Claude Code calls it. Only the standard library: no SDK, no mcp package.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k tutor_mcp_server
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.398s

           OK
       What it checks: initialize, no answer to a notification, tools/list with the three tools, a
       tools/call result, and isError for a wrong date. Add -v to see the name of each test.
    2. By hand: free.
           echo {"jsonrpc": "2.0", "id": 1, "method": "tools/list"} | python agent/tutor_mcp_server.py
               {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "convert_units", "description": "Convert a number ...", ...
           echo {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "convert_units", "arguments": {"value": 1, "from_unit": "mi", "to_unit": "km"}}} | python agent/tutor_mcp_server.py
               {"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "<the result of convert() as JSON text: ... 1.609344 ...>"}], "isError": false}}

IF SOMETHING GOES WRONG
    - Started alone, the program waits and prints nothing: it is waiting for JSON on stdin. Press Ctrl+C.
    - Anything else printed to stdout breaks the connection; print your own messages to stderr.

FILES IT READS AND WRITES
    None.

SEE ALSO
    custom_tools_agent.py (its --cli way starts this server); Lesson 6, Step 8.
"""

import json
import sys

from custom_tools_agent import convert_module, dates_module     # the same skill functions as the SDK way

TOOLS = {
    "convert_units": {
        "description": "Convert a number between units of length, mass, volume, speed, temperature or data size.",
        "inputSchema": {
            "type": "object",
            "properties": {"value": {"type": "number"}, "from_unit": {"type": "string"}, "to_unit": {"type": "string"}},
            "required": ["value", "from_unit", "to_unit"],
        },
        "run": lambda args: convert_module.convert(args["value"], args["from_unit"], args["to_unit"]),
    },
    "weekday": {
        "description": "Day of the week and ISO week number for an ISO date (YYYY-MM-DD).",
        "inputSchema": {"type": "object", "properties": {"date": {"type": "string"}}, "required": ["date"]},
        "run": lambda args: dates_module.weekday(args["date"]),
    },
    "add_business_days": {
        "description": "Add Mon-Fri business days to an ISO date, optionally skipping comma-separated holiday dates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Start date, YYYY-MM-DD"},
                "days": {"type": "integer", "minimum": 0},
                "holidays": {"type": "string", "description": "Comma-separated YYYY-MM-DD dates"},
            },
            "required": ["date", "days"],
        },
        "run": lambda args: dates_module.add_business_days(args["date"], args["days"], args.get("holidays", "")),
    },
}


def handle(request: dict) -> dict | None:
    """One JSON-RPC request in, one response out. None for a notification, which gets no answer."""
    if "id" not in request:
        return None
    method, params = request.get("method"), request.get("params") or {}
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),   # agree to the client's version
            "capabilities": {"tools": {}},                                    # this server offers tools
            "serverInfo": {"name": "tutor", "version": "1.0.0"},
        }
    elif method == "tools/list":
        result = {"tools": [{"name": name, "description": t["description"], "inputSchema": t["inputSchema"]}
                            for name, t in TOOLS.items()]}
    elif method == "tools/call":
        try:
            data = TOOLS[params["name"]]["run"](params.get("arguments") or {})
        except (KeyError, ValueError) as error:          # unknown tool, missing argument, wrong date
            data = {"error": str(error)}
        result = {"content": [{"type": "text", "text": json.dumps(data, default=str)}], "isError": "error" in data}
    elif method == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": request["id"], "result": result}


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")    # plain \n line ends, also on Windows
    for line in sys.stdin:                                     # one JSON-RPC message per line
        if line.strip():
            response = handle(json.loads(line))
            if response is not None:
                print(json.dumps(response), flush=True)
