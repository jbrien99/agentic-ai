from dotenv import load_dotenv
from IPython.display import Image, display
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
load_dotenv(override=True)

@tool
def get_weather(city : str) -> str:
  """ Return today's weather for a city """
  pretend = {"London": "rainy", "Frankfurt": "sunny"}
  return pretend.get(city, "unknown")

memory_agent = create_agent(
  model="openai:gpt-5.4-mini",
  tools=[get_weather],
  checkpointer=MemorySaver(),
  system_prompt="You are a travel assistant. Use your tools to answer questions about cities.",)

config = {"configurable" : {"thread_id": "trip-planning"}}
memory_agent.invoke({"messages": [{"role": "user", "content": "I am planning a trip to London."}]}, config=config)
result = memory_agent.invoke({"messages": [{"role": "user", "content": "What is the weather like where I am going on my trip?"}]}, config=config)
print(result["messages"][-1].content)
