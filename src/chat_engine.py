import os
import sys
import textwrap
from dotenv import load_dotenv

# import your retriever (note: your file is retriver.py)
try:
    from retriver import DocumentRetriever
except Exception as e:
    print("Error importing retriver.DocumentRetriever:", e)
    print("Make sure retriver.py exists in this folder and defines DocumentRetriever.")
    sys.exit(1)

# OpenAI client (you have used openai.OpenAI in other files)
try:
    from openai import OpenAI
except Exception as e:
    print("Error importing OpenAI from openai package:", e)
    print("pip install openai (>=1.0.0) and ensure you're using the package that provides OpenAI class.")
    sys.exit(1)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Missing OPENAI_API_KEY in environment (.env).")
    sys.exit(1)

# Config
TOP_K = int(os.getenv("RAG_TOP_K", "5"))
MODEL = os.getenv("RAG_CHAT_MODEL", "gpt-4.1-mini")  # adjust if you prefer another model
MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "3000"))  # trim context if too long
SHOW_FULL_CHUNKS = os.getenv("RAG_SHOW_FULL_CHUNKS", "false").lower() in ("1", "true", "yes")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Utility: build RAG context from retrieved docs
def build_context(retrieved: list, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """
    retrieved: list of dicts with keys 'content', 'file', 'page', 'distance'
    Return a single string context trimmed to max_chars (approx).
    """
    parts = []
    for i, r in enumerate(retrieved, start=1):
        header = f"--- Retrieved {i} | File: {r.get('file')} | Page: {r.get('page')} | Dist: {r.get('distance'):.4f} ---"
        parts.append(header)
        parts.append(r.get("content", ""))
    context = "\n".join(parts)

    # If context too long, do a simple trim: keep start and end
    if len(context) <= max_chars:
        return context

    head = context[: max_chars // 2]
    tail = context[- (max_chars // 2) :]
    return head + "\n\n... (context trimmed) ...\n\n" + tail

def format_retrieved_for_print(retrieved: list):
    for i, r in enumerate(retrieved, start=1):
        print("-" * 60)
        print(f"Result {i}: File: {r.get('file')} | Page: {r.get('page')} | Distance: {r.get('distance'):.4f}")
        text = r.get("content", "")
        if SHOW_FULL_CHUNKS:
            print("\nText:\n")
            print(textwrap.fill(text, width=120))
        else:
            # print a preview + keep readable line breaks
            preview = text[:1000]
            print("\nText (preview):\n")
            print(textwrap.fill(preview, width=120))
            if len(text) > len(preview):
                print("\n... (truncated preview) ...")
    print("-" * 60)

def ask_llm(question: str, context: str) -> str:
    """
    Sends a chat completion request with context included in the user message.
    Returns assistant content string.
    """
    system_msg = (
        "You are a helpful assistant that uses the provided context (retrieved documents) to answer the user's question. "
        "Prefer to answer from the context and cite source filenames/pages when possible. If the context does not contain the answer, say you don't know."
    )

    user_content = f"Context:\n{context}\n\nQuestion: {question}"

    try:
        resp = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1024,
            temperature=0.0
        )
    except Exception as e:
        return f"[Error calling OpenAI chat completion] {e}"

    # adapt for response shape (assumes standard response)
    try:
        return resp.choices[0].message.content
    except Exception:
        # fallback: try different path
        try:
            return resp.choices[0].text
        except Exception as e:
            return f"[Unexpected response format] {e}"

def main():
    print("\n🔥 RAG Chat Engine (type 'exit' to quit)\n")
    retriever = DocumentRetriever()  # uses persist_dir default from your retriver.py

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            print("Bye.")
            break

        # Step 1: retrieve
        try:
            retrieved = retriever.get_top_k(query, k=TOP_K)
        except Exception as e:
            print("[Error during retrieval]:", e)
            continue

        if not retrieved or len(retrieved) == 0:
            print("No documents retrieved for that query.")
            continue

        # Step 2: show retrievals in terminal (for debugging)
        print("\n📌 Retrieved chunks (top {0}):".format(TOP_K))
        format_retrieved_for_print(retrieved)

        # Step 3: build context & ask LLM
        context = build_context(retrieved)
        print("\n🧠 Asking LLM with RAG context...")
        answer = ask_llm(query, context)

        print("\nAssistant answer:\n")
        print(textwrap.fill(answer, width=120))
        print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
