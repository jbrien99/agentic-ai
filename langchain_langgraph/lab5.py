from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from sidekick_tools import search, send_push_notification, wikipedia_lookup
from sidekick import Sidekick
import asyncio

load_dotenv(override=True)

#My notes.  When creating an agent, you don't provide the task.  You provide a system_prompt simply telling the agent who it is, what is uses for tools, etc...
simple_worker = create_agent(
  model="openai:gpt-5.4-mini",
  tools=[search, send_push_notification, wikipedia_lookup],
  system_prompt="You are a sidekick, a helpful personal assistant. Use your tools to complete the task.",
  checkpointer=InMemorySaver()
)

async def ask(worker, message):
  config = {"configurable": {"thread_id": "simple_sidekick"}}
  result = await worker.ainvoke({"messages": [{"role": "user", "content": message }]},config=config)
  return result["messages"][-1].content

async def main():
  result = await ask(simple_worker, "Search for who won the Nobel Prize in Physics in 2023 and send a push notification with a short summary.")
  print(result)

asyncio.run(main())
