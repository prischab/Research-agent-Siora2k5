# api.py
# FastAPI backend — the bridge between the Next.js frontend and the Siora2k5 agent.
# It exposes the agent over HTTP so a web browser can talk to it.

import os
import base64
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from anthropic import Anthropic
from langchain_core.tools import tool
from langchain.agents import create_agent

from tools.calculator import calculator as _calculator
from tools.web_search import web_search as _web_search
from tools.retrieval import retrieve_docs as _retrieve_docs, ingest_text, ingest_pdf

load_dotenv()

vision_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

VISION_SYSTEM = (
    "You are Siora2k5, an educational research assistant. The user has shared an image. "
    "Describe or analyze it clearly and helpfully in plain text, no emojis. If it contains "
    "text, charts, or diagrams, read and explain them. Be accurate and concise."
)

# --- Define the agent's tools ---
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
    """Search the user's uploaded documents for relevant information."""
    return _retrieve_docs(query)


SYSTEM_PROMPT = (
    "search results. IMPORTANT: Whenever the user refers to a document, paper, file, or anything "
    "they may have uploaded, you MUST call the retrieve_docs tool to search for it before responding. "
    "Never assume no document exists — always search first with retrieve_docs. The user CAN upload "
    "documents, and uploaded content is available through the retrieve_docs tool."
)

agent = create_agent(
    "anthropic:claude-sonnet-4-6",
    tools=[calculator, web_search, retrieve_docs],
    system_prompt=SYSTEM_PROMPT,
)

# --- Build the web app ---
app = FastAPI(title="Siora2k5 API")

# Allow the frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for development; lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/response shapes ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


# --- Endpoints ---
@app.get("/")
def health():
    return {"status": "Siora2k5 is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Receive a question, run the agent, return the answer."""
    result = agent.invoke({"messages": [{"role": "user", "content": req.message}]})
    answer = result["messages"][-1].content
    return ChatResponse(answer=answer)

@app.post("/chat-image")
async def chat_image(file: UploadFile = File(...), message: str = Form("")):
    """Receive an image + optional question, send to Claude's vision, return the answer."""
    contents = await file.read()
    image_b64 = base64.standard_b64encode(contents).decode("utf-8")
    media_type = file.content_type or "image/jpeg"
    user_text = message.strip() or "What is in this image? Describe and explain it."

    response = vision_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=VISION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    answer = "".join(block.text for block in response.content if block.type == "text")
    return {"answer": answer}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Receive an uploaded .txt or .pdf and add it to the knowledge base."""
    contents = await file.read()
    if file.filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        n = ingest_pdf(tmp_path)
        os.unlink(tmp_path)
    else:
        n = ingest_text(contents.decode("utf-8"))
    return {"message": f"Added '{file.filename}' ({n} chunks)."}