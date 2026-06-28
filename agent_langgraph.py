# agent_langgraph.py
# The SAME agent, rebuilt with LangGraph's prebuilt ReAct helper.
# Compare this to agent_from_scratch.py — the framework handles the loop for you.

import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain.agents import create_agent

# Import the same three tool functions we already built
from tools.calculator import calculator as _calculator
from tools.web_search import web_search as _web_search
from tools.retrieval import retrieve_docs as _retrieve_docs

load_dotenv()

# Wrap each function with the @tool decorator so LangGraph understands it.
# The docstring is what the agent reads to decide when to use the tool.
@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Use for any calculation, e.g. '150 * 0.85'."""
    return _calculator(expression)

@tool
def web_search(query: str) -> str:
    """Search the web for current information and facts."""
    return _web_search(query)

@tool
def retrieve_docs(query: str) -> str:
    """Search the local document collection about RAG, agents, vector databases, and evaluation."""
    return _retrieve_docs(query)


SYSTEM_PROMPT = (
    "You are an educational research assistant. Help the user genuinely understand things. "
    "Write in clean plain text, no emojis or decorative headers. Explain clearly, using a short "
    "analogy or example where helpful. For problems needing calculation or research, work through "
    "them step by step. Be accurate and concise, and state your sources when you use search results."
)

# create_react_agent builds the whole agent loop for us — this one line
# replaces the entire while-loop we wrote by hand in agent_from_scratch.py
agent = create_agent(
    "anthropic:claude-sonnet-4-6",
    tools=[calculator, web_search, retrieve_docs],
    system_prompt=SYSTEM_PROMPT,
)


def run_agent(question: str) -> str:
    """Run the LangGraph agent and return the final answer."""
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    # The final answer is the last message in the returned state
    return result["messages"][-1].content


# Test it
if __name__ == "__main__":
    questions = [
        "What is 15% of 2000?",
        "What is a vector database?",
        "What is the current population of Japan, and what would it be if it decreased by 10%?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {run_agent(q)}")