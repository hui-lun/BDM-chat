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

# Node definitions
def spec_search(state: AgentState):
    print("execute spec search")
    print("state_query", state["agent_query"])
    summary = search_database(state["agent_query"])
    print("summary:",summary)
    state["summary"] = summary
    return {
        "summary": summary,
        "next_node": END
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
    # 使用 LLM 判斷 spec_search or web_analyze
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
        "summary": result.get("summary", ""),
        "next_node": END
    }

# State machine schema
graph = StateGraph(AgentState)
graph.add_node("select_tool", select_tool)
graph.add_node("spec_search", spec_search)
graph.add_node("web_analyze", web_analyze)

graph.set_entry_point("select_tool")

graph.add_conditional_edges(
    "select_tool",
    lambda state: state["next_node"]
)

graph.add_edge("spec_search", END)
graph.add_edge("web_analyze", END)

# Compile the graph
app = graph.compile()