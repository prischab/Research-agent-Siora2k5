# tools/retrieval.py
# Document retrieval tool (RAG) — now supports adding documents on the fly.

import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("docs")

# A simple counter so every chunk gets a unique id
_chunk_counter = 0


def _add_chunks(chunks):
    """Embed and store a list of text chunks."""
    global _chunk_counter
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        embedding = embedder.encode(chunk).tolist()
        collection.add(
            ids=[f"chunk_{_chunk_counter}"],
            embeddings=[embedding],
            documents=[chunk],
        )
        _chunk_counter += 1


def ingest_text(text: str):
    """Add raw text (split into paragraph chunks) to the collection. Returns chunk count."""
    chunks = [c for c in text.split("\n\n") if c.strip()]
    _add_chunks(chunks)
    return len(chunks)


def ingest_pdf(filepath: str):
    """Extract text from a PDF and add it in fixed-size chunks. Returns chunk count."""
    import fitz  # PyMuPDF
    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()

    full_text = full_text.strip()
    if not full_text:
        return 0

    chunk_size = 800
    overlap = 100
    chunks = []
    start = 0
    while start < len(full_text):
        chunk = full_text[start:start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap

    _add_chunks(chunks)
    return len(chunks)

def _load_initial_docs():
    """Index any .txt files already in docs/ at startup."""
    for filepath in glob.glob("docs/*.txt"):
        with open(filepath, "r") as f:
            ingest_text(f.read())


_load_initial_docs()


def retrieve_docs(query: str) -> str:
    """Search the indexed documents for text relevant to the query."""
    try:
        if collection.count() == 0:
            return "No documents have been added yet."
        query_embedding = embedder.encode(query).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=3)
        docs = results.get("documents", [[]])[0]
        if not docs:
            return "No relevant documents found."
        return "\n\n".join(f"- {d}" for d in docs)
    except Exception as e:
        return f"Error during retrieval: {e}"


if __name__ == "__main__":
    print(f"Indexed {collection.count()} chunks from docs/")
    print(retrieve_docs("what is a vector database"))