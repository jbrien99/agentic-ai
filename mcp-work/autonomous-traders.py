from dotenv import load_dotenv
import json
from contextlib import AsyncExitStack
from agents import Runner, trace, add_trace_processor
from IPython.display import Markdown, display
from backend.market import get_share_price
from backend.accounts import Account
from backend.accounts_client import read_accounts_resource
from backend.reset import reset_traders
from backend.mcp_servers import trader_mcp_servers, researcher_mcp_servers
from backend.traders import get_researcher, get_researcher_tool, Trader
from backend.tracers import LogTracer

import asyncio

load_dotenv(override=True)

async def snag_researcher_tool(name: str):
  researcher_tool = await get_researcher_tool(researcher_mcp_servers("{name}"), "gpt-5.4-mini")
  print("Tool name:", researcher_tool.name)
  print("Description:", researcher_tool.description)
  return researcher_tool

async def do_research():
  async with AsyncExitStack() as stack:
    servers = [await stack.enter_async_context(server) for server in researcher_mcp_servers("Warreni")]
    researcher = await get_researcher(servers, "gpt-5.4-mini")
    with trace("Researcher"):
      result = await Runner.run(researcher, "What's the latest news on Amazon?", max_turns=30)
  display(Markdown(result.final_output))  
# Very important to not changes in backend/mcp_servers.py
# adding "--with", "mcp<2" to the args
async def list_mcp_servers_and_tools():
  servers = trader_mcp_servers() + researcher_mcp_servers("Warren")
  count = 0
  for server in servers:
    async with server:
      tools = await server.list_tools()
      count += len(tools)
  print(f"We have {len(servers)} MCP servers and {count} tools")

def traders_reset():
  reset_traders() 
  warren = Account.get("Warren")
  print("Balance:", warren.balance)
  print("Strategy:", warren.get_strategy())

async def main():
  await snag_researcher_tool("Warren")
  await list_mcp_servers_and_tools()
  await do_research()

#traders_reset()

asyncio.run(main())
