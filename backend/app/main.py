from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_openai import ChatOpenAI
import os
from fastapi import HTTPException
import requests


DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify url ["http://localhost", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .graph.llm import llm

@app.get("/")
def root():
    return {"message": "LangGraph + LangChain backend running!"}

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str

class AgentChatRequest(BaseModel):
    agent_query: str


class DraftRequest(BaseModel):
    sso_token: str
    subject: str
    body: str
    to_recipients: list[str]


from .graph.graph import app as agent_graph_app, AgentState

@app.post("/agent-chat")
def agent_chat(req: AgentChatRequest):
    state = AgentState(agent_query=req.agent_query, summary="")
    result = agent_graph_app.invoke(state)
    # 回傳完整資訊給前端
    return {
        "summary": result.get("summary", ""),
        "from_email": result.get("from_email", False)
    }


@app.post("/chat")
def chat(req: ChatRequest):
    response = llm.invoke(req.query)
    # force convert to string, avoid [object Object]
    if hasattr(response, "content"):
        text = response.content
    elif hasattr(response, "text"):
        text = response.text
    elif hasattr(response, "message"):
        text = response.message
    else:
        text = str(response)
    return {"response": text}


