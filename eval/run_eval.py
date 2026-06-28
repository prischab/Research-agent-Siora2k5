# eval/run_eval.py
# Evaluation harness: checks that the agent picks the right tool for each question.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_from_scratch import run_agent_with_trace

# Test cases: each question + which tool we EXPECT the agent to use
TEST_CASES = [
    {"question": "What is 25% of 800?", "expected_tool": "calculator"},
    {"question": "What is 144 divided by 12?", "expected_tool": "calculator"},
    {"question": "What is a vector database?", "expected_tool": "retrieve_docs"},
    {"question": "What is retrieval augmented generation?", "expected_tool": "retrieve_docs"},
    {"question": "Who is the current Prime Minister of Japan?", "expected_tool": "web_search"},
    {"question": "What is the latest news about AI regulation?", "expected_tool": "web_search"},
]


def run_evaluation():
    passed = 0
    total = len(TEST_CASES)

    print("Running evaluation...\n")
    for i, case in enumerate(TEST_CASES, 1):
        question = case["question"]
        expected = case["expected_tool"]

        # Run the agent and capture which tools it used
        _, tools_used = run_agent_with_trace(question)

        # Did it use the expected tool?
        correct = expected in tools_used
        passed += correct

        status = "PASS" if correct else "FAIL"
        print(f"{i}. [{status}] '{question}'")
        print(f"     expected: {expected} | used: {tools_used}\n")

    print(f"=== Tool selection accuracy: {passed}/{total} ({round(passed/total*100)}%) ===")


if __name__ == "__main__":
    run_evaluation()