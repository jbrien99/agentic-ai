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

@wrap_tool_call
def log_tool_calls(request, handler):
  call = request.tool_call
  print(f" middleward call {call['name']} with {call['args']}")
  return handler(request)

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

class CityReport(BaseModel):
    city: str = Field(description="The city name")
    weather: str = Field(description="A short weather description")
    population: str = Field(description="The population")

report_agent = create_agent(
    model="openai:gpt-5.4-mini",
    tools=[get_weather, get_population],
    response_format=CityReport,
    middleware=[log_tool_calls],
)

result = report_agent.invoke({"messages": [{"role": "user", "content": "Give me a report on London."}]})
report = result["structured_response"]
print(report)
print("Just the weather:", report.weather)
