import os
import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env variables
dotenv.load_dotenv()

# Import RAG Agent
from chatbot_api.src.chains.hospital_agent import rag_agent

app = FastAPI(title="Gemini RAG Chatbot API", version="1.0")

# Allow UI to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later, restrict this for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    question: str

# Response schema
class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Handle chat requests with RAG Agent"""
    try:
        answer = rag_agent.run(req.question)
        return ChatResponse(answer=answer)
    except Exception as e:
        return ChatResponse(answer=f"Error: {str(e)}")
