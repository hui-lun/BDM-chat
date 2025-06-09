from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
import os
import msgpack
import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi.middleware.cors import CORSMiddleware
from .email_to_db import process_email_to_mongo
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

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

class QAResponse(BaseModel):
    question: str
    answer: str

class QAHistoryResponse(BaseModel):
    title: str
    qa_list: list[QAResponse]

# Load environment variables
load_dotenv()
MONGODB_IP = os.getenv("MONGODB_IP")
MONGODB_USER = os.getenv("MONGODB_USER")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

# Initialize MongoDB connection
uri = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_IP}:27017/admin"
client = MongoClient(uri)
project_col = client["BDM-mgmt"]["BDM-project"]
checkpoint_col = client["checkpointing_db"]["checkpoints"]



from .graph.graph import app as agent_graph_app, AgentState
from .graph.tools.email.email_parse import parse_email_query, mail_format_database 


@app.post("/agent-chat")
def agent_chat(req: AgentChatRequest):
    # Parse email query if it looks like an email
    query = req.agent_query
    is_email = False
    email_info = None
    

    if 'Subject:' in query:
        is_email = True
        email_info = parse_email_query(query)
        logger.info(f"Parsed email info: {email_info}")

        # format for mongoDB
        email = mail_format_database(email_info)
        logger.info(f"Formatted email for database: {email}")
        thread_id_db = process_email_to_mongo(email)
        thread_id = thread_id_db["thread_id"]
        config = {"configurable": {"thread_id": thread_id}}

        # Use the pre-generated summary
        logger.debug(f"Using email summary: {email_info['summary']}")
        state = AgentState(agent_query=email_info['summary'], summary="")
        result = agent_graph_app.invoke(state, config=config)
    else:
        thread_id = uuid.uuid4().hex[:8]
        config = {"configurable": {"thread_id": thread_id}}
        state = AgentState(agent_query=query, summary="")
        result = agent_graph_app.invoke(state, config=config)
    
    logger.debug(f"Request type - is_email: {is_email}")
    
    return {
        "summary": result.get("summary", ""),
        "from_email": is_email
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Get streaming response from LLM
            async for chunk in llm.astream(req.query):
                if hasattr(chunk, "content"):
                    text = chunk.content
                elif hasattr(chunk, "text"):
                    text = chunk.text
                elif hasattr(chunk, "message"):
                    text = chunk.message
                else:
                    text = str(chunk)
                
                yield json.dumps({"token": text}) + "\n"
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            yield json.dumps({"error": error_msg}) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/qa-history/{title}", response_model=QAHistoryResponse)
async def get_qa_history(title: str):
    """
    Get Q&A history for a given title.
    Questions are taken from BDM Email field, answers from checkpoint summary field.
    """
    project_doc = project_col.find_one({"Title": title})
    if not project_doc:
        logger.info(f"No project document found for title: {title}")
        return {"title": title, "qa_list": []}

    thread_id = project_doc.get("thread_id")
    if not thread_id:
        logger.warning(f"No thread_id found for project: {title}")
        return {"title": title, "qa_list": []}

    # Get questions from BDM Email field
    bdm_email_list = project_doc.get("BDM Email", [])
    if not isinstance(bdm_email_list, list) or not bdm_email_list:
        logger.warning(f"No BDM Email list found for project: {title}")
        return {"title": title, "qa_list": []}

    # Get checkpoints for this thread
    qa_list = []
    checkpoints = checkpoint_col.find({"thread_id": thread_id}).sort("checkpoint.ts", -1)

    for i, cp in enumerate(checkpoints):
        raw_cp = cp.get("checkpoint")
        if not raw_cp or i >= len(bdm_email_list):
            continue
        try:
            unpacked = msgpack.unpackb(raw_cp, raw=False)
            cv = unpacked.get("channel_values", {})
            summary = cv.get("summary")

            answer = summary[0] if isinstance(summary, list) else summary
            if answer and answer.strip():
                qa_list.append({
                    "question": bdm_email_list[i],
                    "answer": answer
                })
        except Exception as e:
            logger.error(f"Error processing checkpoint for thread {thread_id}: {e}")
            continue

    logger.info(f"Retrieved {len(qa_list)} Q&A pairs for title: {title}")
    return {"title": title, "qa_list": qa_list}
