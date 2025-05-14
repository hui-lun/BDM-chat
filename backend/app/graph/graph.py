from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from .tools.email.mail_summarize import process_email
from .llm import llm
from .tools.spec.spec_analyze import search_database
from .tools.web.web_analyze import fetch_and_analyze_web_html
from .tools.email.email_reply import generate_email_reply

# State structure
class AgentState(TypedDict):
    agent_query: str
    summary: str
    next_node: str
    from_email: bool

# Node definitions
def spec_search(state: AgentState):
    summary = search_database(state["agent_query"])
    # Check if it comes from email_summarize
    from_email = state.get("from_email", False)
    print(f"from_email: {from_email}")
    next_node = "email_reply" if from_email else ""
    state["summary"] = summary
    return {
        "agent_query": state["agent_query"],
        "summary": summary,
        "next_node": next_node,
        "from_email": from_email
    }


def email_summarize(state: AgentState):
    user_query = process_email(state["agent_query"])
    print(f"summarized_mail:{user_query}")
    # Mark this as an email flow
    return {
        "agent_query": state["agent_query"],
        "summary": user_query,
        "next_node": "spec_search",
        "from_email": True
    }



def email_reply(state: AgentState):
    # Call generate_email_reply to generate a reply based on the summary
    # Convert AgentState to ChatState format if necessary
    print(state["summary"])
    reply_state = generate_email_reply(state["summary"])
    print(reply_state)
    return {"summary": reply_state}


def is_natural_query(text: str) -> bool:
    email_indicators = ["subject:", "dear", "regards", "best", "sincerely", "message", "thank you", "hi"]
    if any(word in text.lower() for word in email_indicators) or len(text.split("\n")) > 5:
        return False
    return True

def select_tool(state: AgentState):
    query = state["agent_query"]
    # 先用 is_natural_query 判斷是不是 email
    if not is_natural_query(query):
        print("[select_tool] Detected as email, using 'email_summarize'.")
        return {"next_node": "email_summarize"}
    # 不是 email 再用 LLM 判斷 spec_search or web_analyze
    prompt = (
        f"Given the user input:'{query}', decide which tool to use:\n"
        "1. If the question is about retrieving data from the database, return 'spec_search'.\n"
        "2. If the question requires analyzing web content, return 'web_analyze'.\n"
        "ONLY return the exact tool name without explanation."
    )
    predicted_label = llm.invoke(prompt).content.strip().lower()
    print(f"[select_tool] Predicted: {predicted_label}")
    return {"next_node": predicted_label}


def web_analyze(state: AgentState):
    print("[web_analyze] called")
    result = fetch_and_analyze_web_html.invoke(state["agent_query"])
    print(f"result: {result}")
    return {
        "agent_query": state["agent_query"],
        "summary": result.get("summary", ""),
        "next_node": ""
    }

# State machine schema
graph = StateGraph(AgentState)
graph.add_node("select_tool", select_tool)
graph.add_node("spec_search", spec_search)
graph.add_node("email_summarize", email_summarize)
graph.add_node("web_analyze", web_analyze)
graph.add_node("email_reply", email_reply)
graph.set_entry_point("select_tool")
graph.add_conditional_edges(
    "select_tool",
    lambda state: state["next_node"]
)
graph.add_edge("email_summarize", "spec_search")
graph.add_conditional_edges(
    "spec_search",
    lambda state: "email_reply" if state.get("from_email") else END
)
graph.add_edge("web_analyze", END)
graph.add_edge("email_reply", END)

# Compile the graph
app = graph.compile()
