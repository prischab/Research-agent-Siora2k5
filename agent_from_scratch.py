# agent_from_scratch.py
# The agent loop, built in plain Python so you understand every piece.

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Import the three tools we built
from tools.calculator import calculator
from tools.web_search import web_search
from tools.retrieval import retrieve_docs

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 1. DESCRIBE the tools to Claude so it knows what it can use
TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate a math expression. Use for any calculation.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "A math expression like '150 * 0.85'"}},
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for current information and facts.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "retrieve_docs",
        "description": "Search the local document collection for relevant information about RAG, agents, vector databases, and evaluation.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to search for in the documents"}},
            "required": ["query"],
        },
    },
]

# 2. MAP tool names to the actual Python functions
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "web_search": web_search,
    "retrieve_docs": retrieve_docs,
}


def run_agent(question: str, verbose: bool = True) -> str:
    """Run the agent loop until it produces a final answer."""
    messages = [{"role": "user", "content": question}]

    # The loop: keep going until Claude stops asking for tools
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=(
                "You are an educational research assistant. Your goal is to help the user "
                "genuinely understand things. Follow these rules:\n"
                "- Write in clean, plain text. No emojis. No decorative headers or dividers.\n"
                "- Explain clearly and simply, as if teaching. Use plain language and, where "
                "helpful, a short analogy or concrete example.\n"
                "- For problems requiring calculation or research, work through them step by step "
                "and show your reasoning, not just the final answer.\n"
                "- Be accurate and concise. When you use search results, state the source.\n"
                "- If something is uncertain or the tools return conflicting information, say so "
                "honestly rather than guessing."
            ),
            tools=TOOLS,
            messages=messages,
        )

        # If Claude wants to use a tool, its stop_reason is "tool_use"
        if response.stop_reason == "tool_use":
            # Add Claude's turn (which includes the tool request) to history
            messages.append({"role": "assistant", "content": response.content})

            # Run each tool Claude asked for
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    if verbose:
                        print(f"  [Agent uses: {tool_name}({tool_input})]")

                    # Call the matching Python function
                    func = TOOL_FUNCTIONS[tool_name]
                    result = func(**tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Feed the tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        else:
            # No more tools needed — Claude gave its final answer
            final = "".join(b.text for b in response.content if b.type == "text")
            return final


def run_agent_with_trace(question: str):
    """Like run_agent, but also returns the list of tools used (for evaluation)."""
    messages = [{"role": "user", "content": question}]
    tools_used = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are an educational research assistant. Answer in clean plain text, no emojis.",
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append(block.name)
                    func = TOOL_FUNCTIONS[block.name]
                    result = func(**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            final = "".join(b.text for b in response.content if b.type == "text")
            return final, tools_used

# Test it
if __name__ == "__main__":
    questions = [
        "What is 15% of 2000?",
        "What is a vector database?",
        "What is the current population of Japan, and what would it be if it decreased by 10%?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        answer = run_agent(q)
        print(f"A: {answer}")