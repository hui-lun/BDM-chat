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
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid
from .graph import api_code
from .graph.tools.email.email_to_db import process_email_to_mongo




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

class TitleGenerationRequest(BaseModel):
    first_message: str

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
async def agent_chat(req: AgentChatRequest):
    query = req.agent_query
    is_email = False
    email_info = None

    if 'Subject:' in query:
        is_email = True
        email_info = parse_email_query(query)
        email = mail_format_database(email_info)
        logger.info(f"email {email}")
        thread_id_db = api_code.call_get_email(email)
        thread_id = thread_id_db["thread_id"]
        config = {"configurable": {"thread_id": thread_id}}
        state = AgentState(agent_query=email_info['summary'], summary="")
    else:
        thread_id = uuid.uuid4().hex[:8]
        config = {"configurable": {"thread_id": thread_id}}
        state = AgentState(agent_query=query, summary="")

    async def event_stream():
        # Send from_email to frontend first
        yield json.dumps({"from_email": is_email}) + "\n"
        result = agent_graph_app.invoke(state, config=config)
        logger.info(f"[agent_chat] Final result: {result}")
        
        # Check if final result needs streaming
        if result.get("needs_streaming"):
            prompt = result["summary"]
            logger.info(f"[agent_chat] Starting LLM streaming for final result")
            # llm stream output 
            async for chunk in llm.astream(prompt):
                
                if hasattr(chunk, "content"):
                    text = chunk.content
                elif hasattr(chunk, "text"):
                    text = chunk.text
                elif hasattr(chunk, "message"):
                    text = chunk.message
                else:
                    text = str(chunk)
                
                logger.debug(f"[agent_chat] Extracted text: '{text}' (length: {len(text)})")
                logger.debug(f"[agent_chat] Streaming chunk: {text}")
                yield json.dumps({"summary": text}) + "\n"
                await asyncio.sleep(0)  # Force immediate sending
        else:
            # Handle results that don't need streaming
            if "summary" in result:
                logger.info(f"[agent_chat] Regular summary: {result['summary'][:100]}...")
                yield json.dumps({"summary": result["summary"]}) + "\n"

    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

                            

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

@app.post("/generate-title")
async def generate_title(req: TitleGenerationRequest):
    """
    Generate a concise title based on the first user message
    """
    try:
        # Create a prompt for title generation
        prompt = f"""
        Based on the user's first message below, generate a concise title (maximum 15 characters).
        The title should:

        1. Capture the core topic or keywords of the message
        2. Be clear and easy to understand
        3. Avoid overly generic or vague terms
        4. Include the product/service name if the user is asking about something specific
        5. Include relevant technical keywords if the message is about a technical issue

        User message: {req.first_message}

        Please return only the title, without any explanation.
        """
                
        # Use the LLM to generate the title
        response = await llm.ainvoke(prompt)
        
        # Extract the title from the response
        if hasattr(response, "content"):
            title = response.content.strip()
        elif hasattr(response, "text"):
            title = response.text.strip()
        else:
            title = str(response).strip()
        
        # Clean up the title (remove quotes, extra spaces, etc.)
        title = title.replace('"', '').replace('"', '').replace('「', '').replace('」', '').strip()
        # If title is too long, truncate it
        if len(title) > 15:
            title = title[:15] + "..."
        
        # If no title generated, use a fallback
        if not title or title.lower() in ['', 'none', 'null', 'undefined']:
            title = "新對話"
        
        logger.info(f"Generated title: '{title}' for message: '{req.first_message[:50]}...'")
        
        return {"title": title}
        
    except Exception as e:
        logger.error(f"Error generating title: {str(e)}")
        return {"title": "新對話"}
