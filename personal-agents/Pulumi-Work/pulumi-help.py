# The imports

import os
import requests
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, trace, function_tool, SQLiteSession
from tools.notifier import push
import asyncio
from pydantic import BaseModel

from mcp_servers import serper_mcp

load_dotenv(override=True)

# 1. Define what a single issue looks like
class CommonPulumiIssue(BaseModel):
  ranking: int
  description: str

# 2. Define the container schema representing the collection
class CommonPulumiIssues(BaseModel):
  issues: list[CommonPulumiIssue] # This forces the model to stream an array of 10 items

async def get_common_errors():

  await serper_mcp.connect()

  agent = Agent(name="PulumiCommonErrors", instructions="You are a python pulumi (Insfrastruce As Code) developer and have a vast knowlege of common errors when using pulumi to deploy Kubernetes resources", model="gpt-5.4-mini", tools=[push], output_type=CommonPulumiIssues, mcp_servers=[serper_mcp])
  # Go to https://platform.openai.com/logs?api=traces to see the traces
  with trace("Top10PulumiErrorsK8s"):
    result = Runner.run_streamed(agent,"Using your mcp  server, determine what are the top 10 most common issues when using Python pulumi to deploy resource to Kubernetes. After preparing the top 10 issues, call the push tool with the list.")
    async for event in result.stream_events():
      if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
      
  return result


async def main():
  result = await get_common_errors()
  print(f"{result.final_output}")

if __name__ == "__main__":
  asyncio.run(main())
