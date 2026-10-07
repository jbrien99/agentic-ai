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

# Define some tools

@tool
def get_weather(city : str) -> str:
  """ Return today's weather for a city """
  pretend = {"London": "rainy", "Frankfurt": "sunny"}
  return pretend.get(city, "unknown")

@tool
def get_population(city: str) -> str:
    """Return the population of a city."""
    pretend = {"London": "8.9 million", "Rome": "2.8 million"}
    return pretend.get(city, "unknown")

agent_with_tools = create_agent(
    model="openai:gpt-5.4-mini",
    tools=[get_weather, get_population],
    system_prompt="You are a travel assistant. Use your tools to answer questions about cities.",
)

result = agent_with_tools.invoke({ "messages": [{"role": "user", "content": "What is the weather and population of London"} ] })
print(result["messages"][-1].content)


do_async = True
async def call_await():
  return await agent.ainvoke({"messages": [{ "role": "user", "content" : "What is the Model Context Protocol, in two sentences?"}] })

async def main():
    if do_async:
        # 3. Added 'await' to execute the coroutine
        result = await call_await()
    else:
        result = agent.invoke({"messages": [{ "role": "user", "content" : "What is the Model Context Protocol, in two sentences?"}] })
    
    print(result["messages"][-1].content)

agent = create_agent(
    model="openai:gpt-5.4-mini",
    system_prompt="You are a helpful assistant who answers concisely.",
)

asyncio.run(main())
