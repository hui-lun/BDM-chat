import os
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.callbacks.base import BaseCallbackHandler

class CustomStreamingHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        print(token, end="", flush=True)

# Create a streaming callback handler
streaming_handler = CustomStreamingHandler()

llm = ChatOpenAI(
    model="gemma-3-27b-it",
    openai_api_key="EMPTY",
    openai_api_base=os.getenv("VLLM_API_BASE", "http://192.168.1.120:8090/v1"),
    streaming=True,
    temperature=0.7,
    max_tokens=2000,
    callbacks=[streaming_handler]
)
