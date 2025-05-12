from O365 import Account
import os
import re
import ast
from langchain_community.tools.office365.events_search import O365SearchEvents
from langchain_community.tools.office365.messages_search import O365SearchEmails
from langchain_community.tools.office365.send_event import O365SendEvent
from langchain_community.tools.office365.send_message import O365SendMessage
from langchain_community.tools.office365.utils import authenticate
from langchain_community.tools.office365.create_draft_message import (
    O365CreateDraftMessage,
)
from langchain_community.agent_toolkits import O365Toolkit
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage


# from langchain_community.agent_toolkits.office365 import tools as o365_tools
from langchain_openai import ChatOpenAI

CLIENT_ID = "e4cd9ba7-9a55-459c-8bfb-ef83d4f725a4"
CLIENT_SECRET = "3Rt8Q~BZU09ODc5o9F2AVPfXlxAw7TrvOrqU-cyI"
TENANT_ID = "9f372369-af15-4cd9-bb9f-8f766d4ee329"


inference_server_url = "http://192.168.1.193:8090/v1"
llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=inference_server_url
)


credentials = (CLIENT_ID, CLIENT_SECRET)
account = Account(credentials, tenant_id=TENANT_ID)
account.connection.refresh_token = ""
toolkit = O365Toolkit(account=account)
mailbox = account.mailbox()
# print("q():", mailbox.q())
# print("mailbox:", mailbox)

O365SearchEvents.model_rebuild()
O365CreateDraftMessage.model_rebuild()
O365SearchEmails.model_rebuild()
O365SendEvent.model_rebuild()
O365SendMessage.model_rebuild()

tools = toolkit.get_tools()
# print(tools)

agent = create_react_agent(llm, tools)

# === 工具語法解析器（簡易正規表達式）===
def extract_tool_args_simple(tool_code_str):
    try:
        match = re.search(r"\[messages_search\((.*?)\)\]", tool_code_str)
        if not match:
            return None
        args_str = match.group(1)
        args = {}
        for pair in re.findall(r'(\w+)\s*=\s*"([^"]+)"', args_str):
            key, value = pair
            args[key] = value
        return args
    except Exception as e:
        print("[Parse Error]", e)
        return None

# === 開始對話 ===
user_input = "list emails send from winny.huang"
response = agent.invoke({"messages": [HumanMessage(content=user_input)]})
print("[1st Agent Output]")
print(response)

# === tool_code fallback 處理 ===
for msg in response.get("messages", []):
    if isinstance(msg, AIMessage) and "```tool_code" in msg.content:
        print("[Detected tool_code fallback]")
        code_block_match = re.search(r"```tool_code\n(.*?)```", msg.content, re.DOTALL)
        if code_block_match:
            tool_code = code_block_match.group(1).strip()
            args = extract_tool_args_simple(tool_code)
            if args:
                print("[Parsed args]", args)
                tool = O365SearchEmails(account=account)
                result = tool.invoke(args)
                print("[Executed Tool Result]")
                print(result)
        break