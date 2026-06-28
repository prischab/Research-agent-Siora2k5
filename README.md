# Siora2k5 — Agentic AI Research Assistant

An AI agent that autonomously selects and chains tools — web search, calculation, and document retrieval — to answer multi-step questions, with a multimodal (image-understanding) chat interface. Built with Claude, FastAPI, and Next.js.

The agent is implemented **two ways** — from scratch and with LangGraph — to demonstrate both the underlying mechanics of agentic loops and the production framework pattern.

**🔗 Live demo:** [research-agent-siora2k5.vercel.app](https://research-agent-siora2k5.vercel.app)
*(Frontend on Vercel, backend on Render. The backend free tier sleeps after inactivity — the first request may take ~50 seconds to wake it.)*

---

## What it does

Siora2k5 is given a question and decides, on its own, which tools it needs:

- **Web search** (Tavily) — for current facts and information
- **Calculator** — for any computation
- **Document retrieval** (RAG) — answers from documents the user uploads
- **Image understanding** (vision) — analyzes uploaded images, charts, and diagrams

It chains tools when needed. For example, *"What is the population of Japan, and what would it be 10% lower?"* triggers a web search followed by a calculation, combined into one sourced answer.

---

## Key features

- **Autonomous tool selection** — the model decides which tool fits each question
- **Multi-step reasoning** — chains multiple tools in sequence
- **Document Q&A (RAG)** — upload a PDF/text file and ask about it; documents persist across conversations
- **Image understanding** — attach an image and ask about it (per-message vision)
- **Chat history** — past conversations saved in a sidebar, with create/switch/delete
- **Evaluation harness** — measures tool-selection accuracy (100% on the test set)
- **Clean custom UI** — chat interface with copy-to-clipboard, built in Next.js

---

## Architecture

```
┌─────────────────┐      HTTP      ┌──────────────────┐      ┌─────────────────┐
│   Next.js UI    │ ─────────────► │   FastAPI API    │ ───► │   Agent (Claude) │
│  chat, sidebar, │ ◄───────────── │  /chat /upload   │ ◄─── │  selects tools,  │
│  upload, vision │                │  /chat-image     │      │  chains, answers │
└─────────────────┘                └──────────────────┘      └─────────────────┘
                                                                      │
                                              ┌───────────────────────┼───────────────────┐
                                              ▼                       ▼                   ▼
                                       web_search (Tavily)      calculator        retrieve_docs
                                                                                  (ChromaDB RAG)
```

**Deployment:** Frontend on Vercel, FastAPI backend on Render. Embeddings run through a hosted API (Cohere) rather than a local model, keeping the backend within serverless memory limits.

---

## Two implementations of the agent

| File | Approach | Purpose |
|---|---|---|
| `agent_from_scratch.py` | Hand-written tool-calling loop | Demonstrates the underlying think → act → observe mechanics |
| `agent_langgraph.py` | LangGraph `create_agent` | Demonstrates the production framework pattern |

Both use the same three tools and produce the same behavior — the contrast shows understanding of agents from first principles *and* the industry-standard toolchain.

---

## Tech stack

| Layer | Tools |
|---|---|
| LLM | Claude (Anthropic API) |
| Agent frameworks | Custom loop + LangGraph |
| Web search | Tavily |
| Retrieval (RAG) | ChromaDB + Cohere embeddings |
| Vision | Claude multimodal |
| Backend | FastAPI (deployed on Render) |
| Frontend | Next.js + Tailwind CSS (deployed on Vercel) |
| Evaluation | Custom pytest-style harness |

---

## Evaluation

A small eval harness (`eval/run_eval.py`) checks whether the agent routes each question to the correct tool:

```
Tool selection accuracy: 6/6 (100%)
```

This reflects the principle that agents must be measured, not just demoed — tool-selection accuracy is the core correctness metric for a tool-using agent.

---

## Project structure

```
research-agent/
├── tools/
│   ├── calculator.py        # calculation tool
│   ├── web_search.py        # Tavily web search tool
│   └── retrieval.py         # RAG document retrieval tool
├── agent_from_scratch.py    # agent loop, hand-written
├── agent_langgraph.py       # agent via LangGraph
├── api.py                   # FastAPI backend (chat, upload, vision)
├── eval/
│   └── run_eval.py          # tool-selection evaluation
├── frontend/                # Next.js chat UI
├── .env.example             # template for required API keys
└── requirements.txt
```

---

## Running locally

**Prerequisites:** Python 3.10+, Node.js, and API keys for Anthropic, Tavily, and Cohere.

```bash
# 1. Backend setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Add your keys: copy .env.example to .env and fill in
#    ANTHROPIC_API_KEY, TAVILY_API_KEY, and COHERE_API_KEY

# 3. Run the backend
uvicorn api:app
#   -> http://127.0.0.1:8000

# 4. Run the frontend (in a second terminal)
cd frontend
npm install
npm run dev
#   -> http://localhost:3000
```

---

## How it was built

Built tool-first: each tool was written and tested in isolation, then the agent loop was implemented by hand to understand the tool-calling mechanics, then rebuilt with LangGraph. The backend wraps the agent over HTTP, and the Next.js frontend adds chat history, document upload, image understanding, and a clean interface. For deployment, the embedding step was moved from a local model to a hosted API to fit the backend within free-tier memory limits.

---

## Possible extensions

- Persist chat history server-side (currently browser storage)
- Add streaming responses (token-by-token)
- Expand the document store with metadata filtering
- Keep the deployed backend warm to avoid cold-start latency

---

> Educational / portfolio project demonstrating agentic AI: tool-calling, multi-step reasoning, RAG, multimodal vision, and evaluation.
