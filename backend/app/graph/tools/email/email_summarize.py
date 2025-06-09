# === Imports ===
import logging
from langchain.prompts import PromptTemplate
from typing_extensions import TypedDict

from ...llm import llm

# Configure logging
logger = logging.getLogger(__name__)


# === Type Definitions ===
class ChatState(TypedDict):
    """
    A dictionary representing the state of a chat session.
    
    Attributes:
    query (str): The content of the email.
    user_query (str): The user's query.
    summary (str): The summary of the user's query.
    """
    query: str
    user_query: str
    summary: str


# === Prompt Templates ===
email_parse_prompt = PromptTemplate.from_template("""
    From the email below, extract and list all clearly specified hardware and requirement details intention in English that describes what information the user wants.
    ===
    {email}
    ===
    Only respond with the query intention.
""")



# === Main Flow ===


def process_email(query: str) -> str:
    """
    Main entry: process email content and return summary from spec_analyze for the chat API.
    """
    logger.info("[mail_summarize] Processing email content")
    try:
        user_query = (email_parse_prompt | llm).invoke({"email": query}).content.strip()
        logger.info(f"[mail_summarize] Extracted user query: {user_query}")
        return user_query
    except Exception as e:
        logger.error(f"[mail_summarize] Error processing email: {str(e)}")
        raise



#
