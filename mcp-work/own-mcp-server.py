from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from IPython.display import display, Markdown

from backend.accounts import Account
import asyncio

load_dotenv(override=True)

async def launch_mcp_server():
  params = {"command": "uv", "args": ["run", "-m", "backend.accounts_server" ]}
  async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
    mcp_tools = await server.list_tools()

async def main():
  return await launch_mcp_server()

asyncio.run(main())
