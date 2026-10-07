import os
import random
import requests
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from IPython.display import Image, display
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv(override=True)

class State(TypedDict):
  messages: Annotated[list, add_messages] # add_messages is a 'reducer', OOTB, does not overwrite 'messages'
  spanish : str  # We do not need a reducer as we want t newly created str each time

nouns = ["Cabbages", "Unicorns", "Toasters", "Penguins", "Bananas", "Eels", "Pickles"]
adjectives = ["outrageous", "smelly", "pedantic", "existential", "sparkly", "haunted"]

def silly_node(state: State) -> dict:
  sentence = f"{random.choice(nouns)} are {random.choice(adjectives)}"
  return {"messages": [{"role" : "assistant", "content": sentence}]}

builder = StateGraph(State)
builder.add_node("silly", silly_node)
builder.add_edge(START, "silly")
builder.add_edge("silly", END)
graph = builder.compile()

display(Image(graph.get_graph().draw_mermaid_png()))

result = graph.invoke({"messages": [{"role": "user", "content": "say something"}]})
print(f"{result}")
print(f"result/messages is: {result["messages"][-1]}")
print(result["messages"][-1].content)

llm = ChatOpenAI(model="gpt-5.4-mini")

def chat_bot(state: State) -> dict:
  return { "messages" : [llm.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("chat_bot", chat_bot)
builder.add_edge(START, "chat_bot")
builder.add_edge("chat_bot", END)
graph = builder.compile()

result = graph.invoke({ "messages": [{"role": "user", "content": "What is a directed graph, in one sentence"}]})

print(result["messages"][-1].content)

#next
search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())

@tool
def send_push_notification(text: str) -> str:
    """Send a short push notification to the user's phone."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={"token": os.getenv("PUSHOVER_TOKEN"), "user": os.getenv("PUSHOVER_USER"), "message": text},
    )
    return "Notification sent"

tools = [search, send_push_notification]
llm_with_tools = llm.bind_tools(tools)
def chat_bot_with_tools(state: State) -> dict:
  return { "messages" : [llm_with_tools.invoke(state["messages"])]}

builder_tools_practice = StateGraph(State)
builder_tools_practice.add_node("chat_bot_with_tools", chat_bot_with_tools)
builder_tools_practice.add_node(ToolNode(tools))

builder_tools_practice.add_edge(START, "chat_bot_with_tools")
builder_tools_practice.add_conditional_edges("chat_bot_with_tools", tools_condition)
builder_tools_practice.add_edge("tools", "chat_bot_with_tools")
graph2 = builder_tools_practice.compile()

graph2.invoke({ "messages" : [{ "role": "user", "content": "Use your search tool to tell me the ingredients of banana bread and send me a push notification."}]})

def translator_node(state: State) -> dict:
  last = state["messages"][-1].content
  prompt = f"Translate this into Spanish, returning only the tranlation.\n\n{last}"
  return { "spanish": llm_with_tools.invoke(prompt).content}

builder_translator = StateGraph(State)
builder_translator.add_node("chat_bot_with_tools", chat_bot_with_tools)
builder_translator.add_node("tools", ToolNode(tools))
builder_translator.add_node("translator", translator_node)

builder_translator.add_edge(START, "chat_bot_with_tools")
builder_translator.add_conditional_edges("chat_bot_with_tools", tools_condition, { "tools": "tools", END: "translator"})
builder_translator.add_edge("tools", "chat_bot_with_tools")
builder_translator.add_edge("translator", END)
graph = builder_translator.compile()

result = graph.invoke({ "messages" : [{"role": "user", "content": "In one sentence, what is special about a banana" }] })
print(result["messages"][-1].content)
print(result["spanish"])


# next
memory = MemorySaver()

builder = StateGraph(State)
builder.add_node("chatbot", chat_bot_with_tools)
builder.add_node("tools", ToolNode(tools))
builder.add_node("translator", translator_node)
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition, {"tools": "tools", END: "translator"})
builder.add_edge("translator", END)
builder.add_edge("tools", "chatbot")
graph = builder.compile(checkpointer=memory)


config = {"configurable": {"thread_id": "conversation-1"}}
graph.invoke({"messages": [{"role": "user", "content": "Hi, my name is Ed."}]}, config)
second = graph.invoke({"messages": [{"role": "user", "content": "What is my name?"}]}, config)
print(second["messages"][-1].content)
print(second["spanish"])

with SqliteSaver.from_conn_string("memory.db") as sql_memory:
    durable_graph = builder.compile(checkpointer=sql_memory)
    sql_config = {"configurable": {"thread_id": "conversation-2"}}
    durable_graph.invoke({"messages": [{"role": "user", "content": "Remember that my favorite color is orange."}]}, sql_config)
    reply = durable_graph.invoke({"messages": [{"role": "user", "content": "What is my favorite color?"}]}, sql_config)
    print(reply["messages"][-1].content)
    print(reply["spanish"])
