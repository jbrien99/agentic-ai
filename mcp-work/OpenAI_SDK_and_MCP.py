# The imports

from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from IPython.display import Image, display
import os
import asyncio

load_dotenv(override=True)

fetch_params = {"command": "uvx", "args": ["--with", "mcp<2","mcp-server-fetch"]}

async def fetch_mcp_tools():
  async with MCPServerStdio(params=fetch_params, client_session_timeout_seconds=60) as server:
      fetch_tools = await server.list_tools()
      print("ran fetch_mcp_tools")
      return fetch_tools
async def fetch_mcp_tools_2():
  async with MCPServerStdio(params=fetch_params, client_session_timeout_seconds=60) as server:
      fetch_tools_2 = await server.list_tools()
      print("ran fetch_mcp_tools_2")
      return fetch_tools_2

async def main():
  result = await fetch_mcp_tools()
  print(f"{result}")
  result = await fetch_mcp_tools_2()
  print(f"{result}")

asyncio.run(main())
