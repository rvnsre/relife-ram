"""Session-scoped MCP stdio server for public, bundled lesson data."""
import argparse
import json
import sys

import learning

VERSION = "2025-11-25"
MAX_FRAME = 8192
MAX_REQUESTS = 2000
UNITS = {"type": "string", "enum": list(learning.UNITS)}
ANNOTATIONS = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}


def schema(**properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


TOOLS = [
    {"name": "education.search_library", "description": "Search bundled Azerbaijani lessons.",
     "inputSchema": schema(query={"type": "string", "minLength": 1, "maxLength": 120})},
    {"name": "education.get_lesson", "description": "Read a bundled lesson by its public ID.",
     "inputSchema": schema(id={"type": "string", "minLength": 1, "maxLength": 80})},
    {"name": "education.convert_units", "description": "Convert length, mass or time.",
     "inputSchema": schema(value={"type": "number", "minimum": -1e100, "maximum": 1e100},
                           source=UNITS, target=UNITS)},
]
BY_NAME = {tool["name"]: dict(tool, annotations=ANNOTATIONS) for tool in TOOLS}


def valid_arguments(arguments, spec):
    if not isinstance(arguments, dict) or set(arguments) != set(spec):
        return False
    for name, rule in spec.items():
        value = arguments[name]
        if rule["type"] == "number":
            if type(value) not in (float, int) or not rule["minimum"] <= value <= rule["maximum"]:
                return False
        elif not isinstance(value, str):
            return False
        elif "enum" in rule:
            if value not in rule["enum"]:
                return False
        elif not rule["minLength"] <= len(value.strip()) <= rule["maxLength"]:
            return False
    return True


class Session:
    def __init__(self, allowed):
        self.allowed = frozenset(allowed)
        self.initialized = False
        self.ready = False
        self.lessons = learning.lessons() if allowed else []

    def tool_call(self, params):
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or name not in self.allowed:
            raise ValueError("Tool is not enabled for this session.")
        if not valid_arguments(arguments, BY_NAME[name]["inputSchema"]["properties"]):
            raise ValueError("Tool arguments do not match its schema.")
        if name == "education.search_library":
            term = arguments["query"].strip().casefold()
            keys = ("id", "subject", "title")
            output = [{key: lesson[key] for key in keys} for lesson in self.lessons if
                      term in " ".join(lesson[key] for key in ("subject", "title", "text")).casefold()]
        elif name == "education.get_lesson":
            output = next((lesson for lesson in self.lessons if lesson["id"] == arguments["id"]), None)
            if output is None:
                return {"isError": True, "content": [{"type": "text", "text": "Bundled lesson not found."}]}
        else:
            try:
                output = {"value": learning.convert(**arguments), "unit": arguments["target"]}
            except ValueError as error:
                return {"isError": True, "content": [{"type": "text", "text": str(error)}]}
        return {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}]}

    def receive(self, message):
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return error(None, -32600, "Invalid Request")
        method = message.get("method")
        params = message.get("params", {})
        if not isinstance(method, str):
            return error(None, -32600, "Invalid Request")
        if "id" not in message:
            if method == "notifications/initialized" and self.initialized:
                self.ready = True
            return None
        request_id = message["id"]
        if type(request_id) not in (int, str):
            return error(None, -32600, "Invalid request ID")
        if not isinstance(params, dict):
            return error(request_id, -32602, "Invalid params")
        if method == "initialize" and not self.initialized:
            if not isinstance(params.get("protocolVersion"), str):
                return error(request_id, -32602, "protocolVersion is required")
            self.initialized = True
            result = {"protocolVersion": VERSION, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "relife-education", "version": "0.3.0"}}
        elif method == "ping":
            result = {}
        elif not self.ready:
            return error(request_id, -32002, "Session is not initialized")
        elif method == "tools/list":
            result = {"tools": [tool for name, tool in BY_NAME.items() if name in self.allowed]}
        elif method == "tools/call":
            try:
                result = self.tool_call(params)
            except ValueError as failure:
                return error(request_id, -32602, str(failure))
        else:
            return error(request_id, -32601, "Method not found")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow", action="append", default=[], choices=sorted(BY_NAME))
    args = parser.parse_args()
    session = Session(args.allow)
    for _ in range(MAX_REQUESTS):
        frame = sys.stdin.buffer.readline(MAX_FRAME + 1)
        if not frame:
            break
        if len(frame) > MAX_FRAME:
            print(json.dumps(error(None, -32700, "Request too large")), flush=True)
            return 1
        try:
            reply = session.receive(json.loads(frame.decode("utf-8")))
        except (UnicodeError, ValueError, RecursionError):
            reply = error(None, -32700, "Parse error")
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=True, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
