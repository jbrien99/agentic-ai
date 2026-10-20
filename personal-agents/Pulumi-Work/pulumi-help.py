import os
import requests
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, trace, function_tool, SQLiteSession
from tools.notifier import push
import asyncio
from pydantic import BaseModel, Field

from mcp_servers import serper_mcp

load_dotenv(override=True)

class CommonPulumiIssue(BaseModel):
  ranking: int
  description: str

class CommonPulumiIssues(BaseModel):
  issues: list[CommonPulumiIssue]

agent = Agent(name="PulumiCommonErrors", instructions="You are a python pulumi (Insfrastruce As Code) developer and have a vast knowlege of common errors when using pulumi to deploy Kubernetes resources", model="gpt-5.4-mini", tools=[push], output_type=CommonPulumiIssues, mcp_servers=[serper_mcp])
solution_agent = Agent(name="PulumiCommonErrors", instructions="You are a python pulumi (Insfrastruce As Code) developer and have a vast knowlege of common solutions to errors when using pulumi to deploy Kubernetes resources", model="gpt-5.4-mini", mcp_servers=[serper_mcp])

async def get_common_errors():
  try:
    # Connect once inside the event loop lifecycle
    await serper_mcp.connect()
  except Exception as e:
    print(f"\n❌ MCP Server may not be defined correctly: {e}")
    return None

  with trace("Top10PulumiErrorsK8s"):
    result = Runner.run_streamed(agent,"Using your mcp server, determine what are the top 10 most common issues when using Python pulumi to deploy resource to Kubernetes. After preparing the top 10 issues, call the push tool with the list.")
    async for event in result.stream_events():
      if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
  return result

async def how_to_fix_common_errors(cpi: CommonPulumiIssues):
  # NOTE: Do NOT call serper_mcp.connect() again if it's already connected in the same loop execution.
  with trace("Top10PulumiErrorsK8sFixes"):
    for i in cpi.issues:
      print(f"\nFind the common solution to {i.description}, ranked as {i.ranking}")
      # Added missing 'f' prefix to evaluate the string template variable properly!
      result = await Runner.run(solution_agent, f"Find the common solution to {i.description}")
      print(f"Solution to {i.description}: {result}")

async def main():
  # 1. Fetch the common errors
  result = await get_common_errors()
  print(f"\nresult is {result}")
  
  if result and hasattr(result, 'final_output') and result.final_output:
    print(f"In find_fixes with {result.final_output}")
    # 2. Run the fixes sequentially inside the same active event loop
    await how_to_fix_common_errors(result.final_output)
  else:
    print("No valid results found to look up fixes for.")

if __name__ == "__main__":
  # The entire sequence now safely shares a single event loop lifecycle
  asyncio.run(main())
