# === Imports ===

from langchain.prompts import PromptTemplate
from typing_extensions import TypedDict

from ...llm import llm


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

summarize_spec_prompt = PromptTemplate.from_template("""
    Extract and list all clearly specified hardware and requirement details from the following user query.
    - Only include what the user explicitly mentioned.
    - just show the list
    ===
    Query:
    {query}
    ===
""")

# === Main Flow ===


def process_email(query: str) -> str:
    """
    Main entry: process email content and return summary from spec_analyze for the chat API.
    """
    user_query = (email_parse_prompt | llm).invoke({"email": query}).content.strip()
    print(f"user_query: {user_query}")
    return user_query



# === Utility Functions ===
def summarize_query(user_query: str) -> str:
    """
    Summarize the user's query.
    
    Args:
    user_query (str): The user's query.
    
    Returns:
    str: The summary of the user's query.
    """
    return (summarize_spec_prompt | llm).invoke({"query": user_query}).content.strip()


