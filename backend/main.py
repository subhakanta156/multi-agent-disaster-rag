# backend.py
import uvicorn
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root and src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agents.workflow.workflow import app
from agents.memory.short_term import ShortTermMemory

# ------------------------------------------------
# GLOBAL SESSION MEMORY STORE
# ------------------------------------------------
SESSION_MEMORY = {}

# -----------------------------
# Input Model
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    session_id: str   # 🔑 REQUIRED FOR MEMORY


# -----------------------------
# Initialize FastAPI
# -----------------------------
backend = FastAPI(
    title="Odisha Disaster Management Assistant Backend",
    version="1.0.0"
)

backend.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# ROOT TEST
# ------------------------------------------------
@backend.get("/")
def root():
    return {"message": "Backend is running", "status": "OK"}


# ------------------------------------------------
# MAIN CHAT ENDPOINT (SESSION AWARE)
# ------------------------------------------------
@backend.post("/chat")
def ask_question(request: QueryRequest):
    try:
        session_id = request.session_id

        # Create memory per session
        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = ShortTermMemory()

        session_memory = SESSION_MEMORY[session_id]

        # Run LangGraph workflow
        result = app.invoke({
            "query": request.query,
            "memory": session_memory,
            "session_id": session_id
        })

        final_answer = result.get("response", "No response generated")

        return {
            "success": True,
            "query": request.query,
            "answer": final_answer,
            "session_id": session_id
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ------------------------------------------------
# SERVER STARTER
# ------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:backend",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
