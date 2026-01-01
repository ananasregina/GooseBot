import asyncio
import json
import os

async def probe_tools():
    # Start goose acp
    proc = await asyncio.create_subprocess_exec(
        "goose", "acp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    def write_json(obj):
        proc.stdin.write(json.dumps(obj).encode() + b"\n")

    async def read_json():
        line = await proc.stdout.readline()
        if not line: return None
        return json.loads(line.decode())

    # Initialize
    write_json({"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "v1", "clientCapabilities": {}, "clientInfo": {"name": "probe"}}, "id": 1})
    init_resp = await read_json()
    
    # List tools - following MCP-like structure if Goose supports it in ACP
    # Actually ACP might expose tools via initialize response or a separate call
    print(f"Initialize response: {json.dumps(init_resp, indent=2)}")

    # Clean up
    proc.terminate()
    await proc.wait()

if __name__ == "__main__":
    asyncio.run(probe_tools())
