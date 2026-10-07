import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv(override=True)

class Company(BaseModel):
  name: str = Field(description="The company name")
  ticker: str = Field(description="The stock ticker symbol")
  founded_year: int = Field(description="The year the company was founded.")

@tool
def get_share_price(symbol: str) -> float:
    """Return the current share price for a given ticker symbol."""
    print(f"I should return data for {symbol}")
    fake_prices = {"AAPL": 241.5, "GOOG": 168.2, "AMZN": 198.0}
    return fake_prices.get(symbol.upper(), 0.0)

#The following 3 print statements work only b.c. it's been annotated with @tool
print("name:", get_share_price.name)
print("description:", get_share_price.description)
print("args:", get_share_price.args)

print("called directly:", get_share_price.invoke({"symbol": "AAPL"}))


llm = ChatOpenAI(model="gpt-5.4-mini")

message = "In 1 sentence, what does it mean for an AI Agent to be autonomous"

straight_invoke = True

if straight_invoke:
  reply = llm.invoke(message)
  print(reply.content)
else:
  for chunk in llm.stream("Tell me a two line poem about autonomous agents"):
     print(chunk.content, end="", flush=True)

straight_dicts = True
if straight_dicts == False:
  messages = [
    SystemMessage("You are a terse assistant who answers in exactly five words."),
    HumanMessage("What is the capital of France?"),
  ]
  print(llm.invoke(messages).content)
else:
  # The exact same call using plain dictionaries, the format you already know
  messages_as_dicts = [
    {"role": "system", "content": "You are a terse assistant who answers in exactly five words."},
    {"role": "user", "content": "What is the capital of France?"},
  ]
  print(llm.invoke(messages_as_dicts).content)

llm_with_tools = llm.bind_tools([get_share_price])
response = llm_with_tools.invoke("What is the share price of Amazon?")
# IMPORTANT - the invoke above does NOT call that tool.  
print("content:", repr(response.content))
print("tool_calls:", response.tool_calls)

# Start the conversation and keep the model's tool request in the history
conversation = [HumanMessage("What is the share price of Amazon?")]
ai_message = llm_with_tools.invoke(conversation)
conversation.append(ai_message)

for call in ai_message.tool_calls:
  if call['name'] == "get_share_price":
    result = get_share_price.invoke(call['args'])
    conversation.append(ToolMessage(content=str(result), tool_call_id=call['id']))

# Call again, not that model can see the tool result
final = llm_with_tools.invoke(conversation)
print(final.content)

structured_llm = llm.with_structured_output(Company)
company = structured_llm.invoke("Tell me about Amazon the technology company")
print(company)
