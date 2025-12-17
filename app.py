import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.main import ask_question, QueryRequest

# Initialize FastAPI app
app = FastAPI(title="Odisha Disaster Management Assistant")

# Register the chat endpoint from backend
app.post("/chat")(ask_question)

# Mount the 'frontend' directory to serve static files
# html=True allows serving index.html at root '/'
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Hugging Face Spaces typically expects port 7860
    uvicorn.run(app, host="0.0.0.0", port=7860)
