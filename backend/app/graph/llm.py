import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE", "http://192.168.1.193:8090/v1")
)
