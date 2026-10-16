# The imports

import os
import requests
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, trace, function_tool, SQLiteSession
import asyncio
load_dotenv(override=True)

async def get_common_errors():
  agent = Agent(name="PulumiCommonErrors", instructions="You are a python pulumi (Insfrastruce As Code) developer and have a vast knowlege of common errors when using pulumi to deploy Kubernetes resources", model="gpt-5.4-mini")
  # Go to https://platform.openai.com/logs?api=traces to see the traces
  with trace("Top10PulumiErrorsK8s"):
    result = Runner.run_streamed(agent,"What are the top 10 most common issues when using Python pulumi to deploy resource to Kubernetes")
    async for event in result.stream_events():
      if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
        print(event.data.delta, end="", flush=True)
  return result


async def main():
  result = await get_common_errors()
  print(f"{result.final_output}")

if __name__ == "__main__":
  asyncio.run(main())
