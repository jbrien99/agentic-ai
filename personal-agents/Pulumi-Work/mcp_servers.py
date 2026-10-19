import os
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio

load_dotenv()

serper_mcp = MCPServerStdio(
  name="serper-search",
  params={
    "command": "npx",
    "args":["-y", "serper-search-scrape-mcp-server"],
    "env": {
      **os.environ,
      "SERPER_API_KEY": os.environ.get("SERPER_API_KEY", "")
    },
  },
)
