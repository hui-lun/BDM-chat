import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE", "http://192.168.1.120:8090/v1"),
    streaming=True,  # Enable streaming
    temperature=0.7,
    max_tokens=2000
)
