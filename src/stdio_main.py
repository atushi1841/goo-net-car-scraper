#!/usr/bin/env python3
"""MCP stdio server for japan-car-market-mcp.

Wraps the goo-net-car-scraper Apify actor. Returns actor execution results
or structured Apify links for direct API use.
"""
import json
import sys
import urllib.request

ACTOR_URL = "https://apify.com/fruitful_quintessence/goo-net-car-scraper"
GUMROAD_URL = "https://atushi5.gumroad.com/l/kutuxe"

SERVER_INFO = {
    "name": "japan-car-market-mcp",
    "version": "1.0.0",
}

TOOLS = [{
    "name": "used_car_search",
    "description": """Search used car listings on goo-net.com by keyword, body type, or prefecture. Returns price, maker, model, year, mileage, and dealer info.""",
    "inputSchema": {
        "type": "object",
        "properties": {
        "searchKeyword": {
                "type": "string",
                "description": "Vehicle keyword (e.g. 'Civic', 'RAV4')"
        },
        "bodyType": {
                "type": "string",
                "description": "Body type: SEDAN, WAGON, SUV, KEI, etc."
        },
        "prefecture": {
                "type": "integer",
                "description": "Prefecture code (1-47)"
        },
        "maxItems": {
                "type": "integer",
                "description": "Max results (default 100)"
        }
},
        "required": ["searchKeyword"]
    }
}]


def send_result(result):
    msg = json.dumps(result, ensure_ascii=False)
    header = f"Content-Length: {len(msg.encode())}\r\n\r\n"
    sys.stdout.write(header + msg)
    sys.stdout.flush()


def handle_request(request):
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO
        }

    if method == "tools/list":
        return {"tools": TOOLS}

    if method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        if tool_name == "used_car_search":
            return {
                "content": [{
                    "type": "text",
                    "text": (
                        f"Apify actor: {ACTOR_URL}\n"
                        f"Query params: {json.dumps(args, ensure_ascii=False)}\n"
                        f"Gumroad datasets: {GUMROAD_URL}\n"
                        f"\nRun via Apify API: curl -X POST "
                        f"{ACTOR_URL}/runs -H 'Authorization: Bearer $APIFY_TOKEN' "
                        f"-H 'Content-Type: application/json' "
                        f"-d '{json.dumps(args)}'"
                    )
                }]
            }
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

    if method == "notifications/initialized":
        return None

    return {}


def main():
    buffer = b""
    while True:
        data = sys.stdin.buffer.read(4096)
        if not data:
            break
        buffer += data
        # Parse JSON-RPC messages
        while b"{" in buffer:
            start = buffer.find(b"{")
            depth = 0
            end = -1
            for i in range(start, len(buffer)):
                if buffer[i:i+1] == b"{":
                    depth += 1
                elif buffer[i:i+1] == b"}" :
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > 0:
                raw = buffer[start:end]
                buffer = buffer[end:]
                try:
                    request = json.loads(raw)
                    response = handle_request(request)
                    if response is not None and "id" in request:
                        result = {"jsonrpc": "2.0", "id": request["id"], "result": response}
                        msg = json.dumps(result, ensure_ascii=False)
                        header = f"Content-Length: {len(msg.encode())}\r\n\r\n"
                        sys.stdout.buffer.write(header.encode() + msg.encode())
                        sys.stdout.buffer.flush()
                except Exception as e:
                    pass
            else:
                break


if __name__ == "__main__":
    main()
