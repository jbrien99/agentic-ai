import os
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from crewai_tools import DirectoryReadTool, FileReadTool
from crewai.tools import BaseTool

load_dotenv(override=True)
print(f'api_key is {os.environ["OPENAI_API_KEY"]}')
print(f'model is {os.environ["MODEL"]}')

sales_rep_agent = Agent(
  role="Sales Representative",
  goal="Identify high-value leads that match our ideal customer profile",
  backstory=("As part of the dynamic sales team as CrewAI, your mission is to scour the digital landscape for potential leads "),
  allow_delegation=False,
  verbose=True)

lead_sales_rep_agent = Agent(
  role="Lead Sales Representative",
  goal="Nurture leads with personlized, compelling emails",
  backstory=("Within the vibrant ecosystem of CrewAIs sales department, you stand out as the bridge between potential clients and the solutions they need. "),
  allow_delegations=False,
  verbose=True
)

class ReadLocalDirectoryAndFiles(BaseTool):
  name : str = "ReadLocalDirectoryAndFiles"
  description : str = ("Read a local directory and the files in it")
  
  def _run(self, argument: str) -> str:
    return "positive"

directory_read_tool = DirectoryReadTool('.instructions')
file_read_tool = FileReadTool('.instructions/1.txt')
rldaf = ReadLocalDirectoryAndFiles()

lead_profiling_task = Task(
  description=(
    "Conduct an in-depth analysis of {lead_name}, a company in {industry} sector that recently show interest in  our product. Utilize web searches, but limit it to 2 searches. "
  ),
  expected_output=(
    "A detailed report on {lead_name}, providing a list of 3 lead, including company name and email if possible."
  ),
  tools=[directory_read_tool, file_read_tool],
  agent=sales_rep_agent
)

personalized_outreach_task = Task (
  description=("

)

if __name__ == '__main__':
  print("main")
