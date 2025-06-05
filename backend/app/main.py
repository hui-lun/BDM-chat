from fastapi import FastAPI, Depends, HTTPException
from langchain_openai import ChatOpenAI
import os
import msgpack
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .email_to_db import process_email_to_mongo
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid
import json
import asyncio
from typing import AsyncGenerator

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

from .graph.tools.email.mail_summarize import process_email

# format for mongoDB
def mail_format_database(email_info: dict) -> dict:
    """
    將 email_info 格式轉換成標準格式：
    {
        "Title": ..., "Company Name": ..., "BDM": ...,
        "Summary": ..., "datetime_str": ...
    }
    """

    title = email_info.get("subject", "(無主旨)")
    company_name = email_info.get("from", "(無寄件者)")
    bdm = email_info.get("to", "(無收件者)")
    summary = email_info.get("summary", "(無摘要)")
    email = email_info.get("email", "(無內容)")
    raw_date = email_info.get("date", "")
    raw_date = raw_date.split(" (")[0] 
    # time format
    try:    
        dt = datetime.strptime(raw_date, "%a %b %d %Y %H:%M:%S GMT%z")
        datetime_str = dt.strftime("%Y/%-m/%-d %-I:%M %p")
    except Exception as e:
        print(f"[convert_email_info] 日期格式錯誤: {e}")
        datetime_str = raw_date  # fallback raw date

    # all format
    email = {
        "Title": title,
        "Company Name": company_name,
        "BDM": bdm,
        "Summary": summary,
        "datetime_str": datetime_str,
        "Email": email
    }

    return email


def parse_email_query(query: str) -> dict:
    """Parse email query string into a dictionary of email information and generate summary.
    Expected format:
    Subject: <subject>
    From: <sender>
    To: <recipients>
    Date: <datetime>
    email: <query>
    <body>
    """
    lines = query.split('\n')
    email_info = {}
    body_lines = []
    in_body = False
    
    for line in lines:
        line = line.strip()
        if not line and not in_body:
            in_body = True
            continue
            
        if in_body:
            body_lines.append(line)
        else:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                email_info[key] = value
    
    body = '\n'.join(body_lines).strip()
    email_info['body'] = body
    email_info['email'] = query
    # Generate summary using process_email
    email_info['summary'] = process_email(body)

    return email_info

@app.post("/agent-chat")
async def agent_chat(req: AgentChatRequest):
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Parse email query if it looks like an email
            query = req.agent_query
            is_email = False
            email_info = None

            if 'Subject:' in query:
                is_email = True
                email_info = parse_email_query(query)
                print("Parsed email info:", email_info)

                # format for mongoDB
                email = mail_format_database(email_info)
                print("email_info_bill:", email)
                thread_id_db = process_email_to_mongo(email)
                thread_id = thread_id_db["thread_id"]
                config = {"configurable": {"thread_id": thread_id}}

                # Use the pre-generated summary
                print(email_info['summary'])
                state = AgentState(agent_query=email_info['summary'], summary="")
                result = agent_graph_app.invoke(state, config=config)
            else:
                thread_id = uuid.uuid4().hex[:8]
                config = {"configurable": {"thread_id": thread_id}}
                state = AgentState(agent_query=query, summary="")
                result = agent_graph_app.invoke(state, config=config)

            print("is_email", is_email)
            
            # Get the response text
            response_text = result.get("summary", "")
            
            # Stream each character with a small delay
            for char in response_text:
                yield json.dumps({
                    "token": char,
                    "from_email": is_email
                }) + "\n"
                await asyncio.sleep(0.01)  # Small delay to make streaming visible
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            yield json.dumps({"error": error_msg}) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream"
        }
    )


@app.post("/chat")
async def chat(req: ChatRequest):
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Get streaming response from LLM
            response = await llm.ainvoke(req.query)
            
            # Handle different response types
            if hasattr(response, "content"):
                text = response.content
            elif hasattr(response, "text"):
                text = response.text
            elif hasattr(response, "message"):
                text = response.message
            else:
                text = str(response)
            
            # Stream each character with a small delay
            for char in text:
                yield json.dumps({"token": char}) + "\n"
                await asyncio.sleep(0.01)  # Small delay to make streaming visible
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
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
        return {"title": title, "qa_list": []}

    thread_id = project_doc.get("thread_id")
    if not thread_id:
        return {"title": title, "qa_list": []}

    # Get questions from BDM Email field
    bdm_email_list = project_doc.get("BDM Email", [])
    if not isinstance(bdm_email_list, list) or not bdm_email_list:
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
            print(f"Error processing checkpoint: {e}")
            continue

    return {"title": title, "qa_list": qa_list}
