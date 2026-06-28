# tools/retrieval.py
# Document retrieval (RAG) using Cohere embeddings + ChromaDB.
# Cohere runs as an API call, so no heavy local model loads into memory
# (this is what lets it fit in Render's 512MB free tier).

import os
import cohere
import chromadb

# Cohere client reads COHERE_API_KEY from the environment
_co = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
_EMBED_MODEL = "embed-english-v3.0"

# In-memory Chroma collection (resets on restart, which is fine for a demo)
_client = chromadb.Client()
_collection = _client.get_or_create_collection("documents")

# Simple counter so each chunk gets a unique id
_counter = {"n": 0}


def _embed(texts: list[str], input_type: str) -> list[list[float]]:
    """Turn a list of texts into embeddings via the Cohere API.
    input_type is 'search_document' for stored chunks, 'search_query' for queries."""
    result = _co.embed(
        texts=texts,
        model=_EMBED_MODEL,
        input_type=input_type,
        embedding_types=["float"],
    )
    return result.embeddings.float


def _add_chunks(chunks: list[str]):
    """Embed chunks and store them in ChromaDB."""
    if not chunks:
        return
    embeddings = _embed(chunks, "search_document")
    ids = []
    for _ in chunks:
        ids.append(f"chunk_{_counter['n']}")
        _counter["n"] += 1
    _collection.add(documents=chunks, embeddings=embeddings, ids=ids)


def ingest_text(text: str) -> int:
    """Chunk raw text and add it to the store. Returns chunk count."""
    text = text.strip()
    if not text:
        return 0
    chunk_size = 800
    overlap = 100
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    _add_chunks(chunks)
    return len(chunks)


def ingest_pdf(filepath: str) -> int:
    """Extract text from a PDF and add it in fixed-size chunks. Returns chunk count."""
    import fitz  # PyMuPDF
    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return ingest_text(full_text)


def retrieve_docs(query: str, k: int = 4) -> str:
    """Find the most relevant chunks for a query. Returns them as joined text."""
    count = _collection.count()
    if count == 0:
        return "No documents have been uploaded yet."

    query_embedding = _embed([query], "search_query")[0]

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, count),
    )
    docs = results.get("documents", [[]])[0]
    if not docs:
        return "No relevant content found in the uploaded documents."
    return "\n\n---\n\n".join(docs)