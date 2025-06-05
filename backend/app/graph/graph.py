import json
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from .tools.email.mail_summarize import process_email
from .llm import llm
from .tools.spec.spec_analyze import search_database
from .tools.web.web_analyze import fetch_and_analyze_web_html
from .tools.email.email_reply import generate_email_reply
from .tools.mgmt.manage import get_manage_data
from .tools.mgmt.pretty_output import pretty_print_projects
from .checkpoint import get_checkpointer

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
    if summary == "database not found this server":
        return{
            "next_node": "web_analyze"
        }
    else:
        print("summary:",summary)
        state["summary"] = summary
        return {
            "summary": summary,
            "next_node": END
        }
    
# def email_reply(state: AgentState):
#     # Call generate_email_reply to generate a reply based on the summary
#     # Convert AgentState to ChatState format if necessary
#     print(state["summary"])
#     reply_state = generate_email_reply(state["summary"])
#     print(reply_state)
#     return {"summary": reply_state}


def is_natural_query(text: str) -> bool:
    email_indicators = ["subject:", "dear", "regards", "best", "sincerely", "message", "thank you", "hi"]
    if any(word in text.lower() for word in email_indicators) or len(text.split("\n")) > 5:
        return False
    return True

def select_tool(state: AgentState):
    query = state["agent_query"]
    # let llm decide where to go : spec_search or web_analyze
    prompt = (
        f"Given the user input:'{query}', decide which tool to use:\n"
        "1. If the question is about retrieving data from the database, return 'spec_search'.\n"
        "2. If the question requires analyzing web content, return 'web_analyze'.\n"
        "ONLY return the exact tool name without explanation."
        "3. If the question is about BDM reports, updates, or contains a person's name (e.g., gary.yccheng, alice.wang) "
        "and/or time period (e.g., this week, monthly, quarterly, this year), return 'manage'.\n"
        "ONLY return the exact tool name without explanation."

    )
    predicted_label = llm.invoke(prompt).content.strip().lower()
    print(f"[select_tool] Predicted: {predicted_label}")
    return {"next_node": predicted_label}

# def select_tool(state: AgentState):
#     query = state["agent_query"]
    # 使用 LLM 判斷 spec_search or web_analyze
    # prompt = (
    #     f"Given the user input:'{query}', decide which tool to use:\n"
    #     "1. If the question is about retrieving data from the database, return 'spec_search'.\n"
    #     "2. If the question requires analyzing web content, return 'web_analyze'.\n"
    #     "3. If the question is about BDM reports, updates, or contains a person's name (e.g., gary.yccheng, alice.wang) "
    #     "and/or time period (e.g., this week, monthly, quarterly, this year), return 'manage'.\n"
    #     "ONLY return the exact tool name without explanation."
    # )
    # prompt = f"""
    # Analyze this query and select the appropriate tool:

    # Query: "{query}"

    # Tool Selection Guidelines:
    
    # USE 'web_analyze' FOR:
    # - Any hardware specifications (TDP, cores, clock speeds, etc.)
    # - Product specifications and details
    # - Compatibility questions
    # - Technical comparisons
    # - Release dates, EOL dates, product lifecycles
    # - Part numbers, model numbers, SKUs
    # - Form factors, dimensions, physical specifications
    # - Power requirements, cables, connectors
    # - Any question that might require looking up product documentation or specifications

    # USE 'spec_search' ONLY FOR:
    # - Queries about internal database records that you're certain exist in our system
    # - Specific internal product data that's not publicly available

    # USE 'manage' ONLY FOR:
    # - BDM reports
    # - Team updates
    # - Queries containing team member names (e.g., gary.yccheng, alice.wang)
    # - Time-based reports (weekly, monthly, quarterly)

    # Examples that should use 'web_analyze':
    # - "What is the TDP of RTX 6000 ADA?"
    # - "How many PCIe slots does R263-ZG0-AAL2 have?"
    # - "When is AMD Milan going EOL?"
    # - "What type of power cable does Alveo V80 use?"

    # IMPORTANT: When in doubt, choose 'web_analyze'.

    # Return ONLY the tool name in lowercase.
    # """
    # predicted_label = llm.invoke(prompt).content.strip().lower()
    # print(f"[select_tool] Predicted: {predicted_label}")
    # return {"next_node": predicted_label}




def web_analyze(state: AgentState):
    print("[web_analyze] called")
    result = fetch_and_analyze_web_html.invoke(state["agent_query"])
    print(f"result: {result}")
    return {
        "summary": result.get("summary", ""),
        "next_node": END
    }


def llm_answer(state: AgentState):
    print("[llm_answer] called")
    response = llm.invoke(state["agent_query"])
    print(response)
    return {
        "summary": response.content,
        "next_node": END
    }


def manage(state: AgentState):
    print("[manage] called")
    query = state["agent_query"]
    print(f"Processing BDM query: {query}")
    
    try:
        # Get the raw result from get_manage_data
        result = get_manage_data.invoke(query)
        # Convert the result to a string that can be displayed in the frontend
        if isinstance(result, dict) and 'response' in result :
            print('go 1111')
            # If the result already has a 'response' field (from get_bdm_response)
            response_text = result['response']
            data = response_text
            if not ('"type": "chart"' in str(response_text)):
                    print("Not a chart response, formatting data...")
                    response_text = pretty_print_projects(data)
            # response_text = pretty_print_projects(data)
            print("go 1")
        else:
            # Otherwise, convert the result to a JSON string
            response_text = json.dumps(result, ensure_ascii=False, indent=2)
            data = json.loads(response_text)
            response_text = pretty_print_projects(data)
            print("go 2")
        print(f"Sending response to frontend: {response_text}...")
        
        return {
            "summary": response_text,  # This will be displayed in the chat
            "next_node": END
        }
        
    except Exception as e:
        error_msg = f"Error processing BDM query: {str(e)}"
        print(error_msg)
        return {
            "next_node": "llm_answer"
        }


# State machine schema
graph = StateGraph(AgentState)
graph.add_node("select_tool", select_tool)
graph.add_node("spec_search", spec_search)
graph.add_node("web_analyze", web_analyze)
graph.add_node("llm_answer", llm_answer)
graph.add_node("manage", manage)

graph.set_entry_point("select_tool")

graph.add_conditional_edges(
    "select_tool",
    lambda state: state["next_node"]
)

graph.add_conditional_edges(
    "spec_search",
    lambda state: state["next_node"]
)

graph.add_conditional_edges(
    "manage",
    lambda state: state["next_node"]
)

graph.add_edge("spec_search", END)
graph.add_edge("web_analyze", END)
graph.add_edge("manage", END)

# Compile the graph
checkpointer = get_checkpointer()
app = graph.compile(checkpointer=checkpointer)