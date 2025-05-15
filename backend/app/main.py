from fastapi import FastAPI, Depends
from langchain_openai import ChatOpenAI
import os
from datetime import datetime
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

from .graph.tools.email.mail_summarize import process_email

#For Bill
def mail_format_database(email_info: dict) -> dict:
    """
    將 email_info 格式轉換成標準格式：
    {
        "Title": ..., "Customer Name": ..., "BDM": ...,
        "Summary": ..., "datetime_str": ...
    }
    """

    title = email_info.get("subject", "(無主旨)")
    customer = email_info.get("from", "(無寄件者)")
    bdm = email_info.get("to", "(無收件者)")
    summary = email_info.get("summary", "(無摘要)")
    raw_date = email_info.get("date", "")
    raw_date = raw_date.split(" (")[0] 
    # time format
    try:    
        dt = datetime.strptime(raw_date, "%a %b %d %Y %H:%M:%S GMT%z")
        datetime_str = dt.strftime("%Y/%-m/%-d %-I:%M %p")
    except Exception as e:
        print(f"[convert_email_info] 日期格式錯誤: {e}")
        datetime_str = raw_date  # fallback 原始字串

    # 組合格式
    email = {
        "Title": title,
        "Customer Name": customer,
        "BDM": bdm,
        "Summary": summary,
        "datetime_str": datetime_str
    }

    return email


def parse_email_query(query: str) -> dict:
    """Parse email query string into a dictionary of email information and generate summary.
    Expected format:
    Subject: <subject>
    From: <sender>
    To: <recipients>
    Date: <datetime>
    
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
    
    # Generate summary using process_email
    email_info['summary'] = process_email(body)


    return email_info

@app.post("/agent-chat")
def agent_chat(req: AgentChatRequest):
    # Parse email query if it looks like an email
    query = req.agent_query
    is_email = False
    email_info = None
    
    if 'Subject:' in query:
        is_email = True
        email_info = parse_email_query(query)
        print("Parsed email info:", email_info)

        #FOR Bill
        email = mail_format_database(email_info) 
        print("email_info_bill:",email)

        # Use the pre-generated summary
        print(email_info['summary'])
        state = AgentState(agent_query=email_info['summary'], summary="")
    else:
        state = AgentState(agent_query=query, summary="")
    
    print("is_email",is_email)
    result = agent_graph_app.invoke(state)
    print("result", result)
    
    return {
        "summary": result.get("summary", ""),
        "from_email": is_email
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

