import json
import logging
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from .llm import llm
from .tools.spec.spec_analyze import search_database
from .tools.web.web_analyze import fetch_and_analyze_web_html
from .tools.mgmt.manage import get_manage_data
from .tools.mgmt.pretty_output import pretty_print_projects
from .checkpoint import get_checkpointer
from .markdown_output import markdown_output

# Configure logging
logger = logging.getLogger(__name__)

# State structure
class AgentState(TypedDict):
    agent_query: str
    summary: str
    next_node: str

# Node definitions
def spec_search(state: AgentState):
    logger.info("[spec_search] Executing spec search")
    logger.debug(f"Query: {state['agent_query']}")
    summary = search_database(state["agent_query"])
    if summary == "database not found this server":
        logger.info("[spec_search] No database found, redirecting to web_analyze")
        return {
            "next_node": "web_analyze"
        }
    else:
        logger.info(f"[spec_search] Found summary: {summary}")
        # summary = markdown_output(summary)
        state["summary"] = summary
        return {
            "summary": summary,
            "next_node": "beauty_output"
        }
    


def select_tool(state: AgentState):
    query = state["agent_query"]
    logger.info("[select_tool] Determining tool selection")
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
    logger.info(f"[select_tool] Selected tool: {predicted_label}")
    return {"next_node": predicted_label}



def web_analyze(state: AgentState):
    logger.info("[web_analyze] Processing web analysis request")
    result = fetch_and_analyze_web_html.invoke(state["agent_query"])
    logger.info(f"[web_analyze] Analysis result: {result}")
    return {
        "summary": result.get("summary", ""),
        "next_node": END
    }


def llm_answer(state: AgentState):
    logger.info("[llm_answer] Processing LLM request")
    response = llm.invoke(state["agent_query"])
    logger.debug(f"[llm_answer] LLM response: {response}")
    return {
        "summary": response.content,
        "next_node": END
    }


def beauty_output(state: AgentState):
    logger.info("[beauty_output] generate response with markdown format")
    markdown = markdown_output(state["summary"])
    return {
        "summary": markdown,
        "next_node": END
    }


def manage(state: AgentState):
    logger.info("[manage] Processing BDM management request")
    query = state["agent_query"]
    logger.debug(f"[manage] Query: {query}")
    
    try:
        # Get the raw result from get_manage_data
        result = get_manage_data.invoke(query)
        # Convert the result to a string that can be displayed in the frontend
        if isinstance(result, dict) and 'response' in result :
            logger.debug("[manage] Processing response with 'response' field")
            # If the result already has a 'response' field (from get_bdm_response)
            response_text = result['response']
            data = response_text
            if not ('"type": "chart"' in str(response_text)):
                    logger.debug("[manage] Formatting non-chart response")
                    response_text = pretty_print_projects(data)
            # response_text = pretty_print_projects(data)
                    # response_text = pretty_print_projects(data)
                    # response_text = markdown_output(response_text)

            logger.debug("[manage] Successfully processed BDM query")
        else:
            logger.debug("[manage] Converting result to JSON and formatting")
            # Otherwise, convert the result to a JSON string
            response_text = json.dumps(result, ensure_ascii=False, indent=2)
            data = json.loads(response_text)
            response_text = pretty_print_projects(data)
            
            logger.debug("[manage] Successfully processed BDM query")
        logger.info("[manage] Sending response to frontend: {response_text}...")
        
        return {
            "summary": response_text,  # This will be displayed in the chat
            "next_node": "beauty_output"
        }
        
    except Exception as e:
        error_msg = f"Error processing BDM query: {str(e)}"
        logger.error(f"[manage] {error_msg}")
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
graph.add_node("beauty_output", beauty_output)

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

# graph.add_edge("spec_search", "beauty_output")
graph.add_edge("web_analyze", END)
# graph.add_edge("manage", beauty_output)
graph.add_edge("beauty_output", END)

# Compile the graph
checkpointer = get_checkpointer()
app = graph.compile(checkpointer=checkpointer)