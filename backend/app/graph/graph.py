import logging
from langgraph.graph import StateGraph, END
from .checkpoint import get_checkpointer
from .nodes import (
    AgentState,
    select_tool,
    spec_search,
    web_analyze,
    llm_answer,
    manage,
    beauty_output_text,
    beauty_output_web
)

# Configure logging
logger = logging.getLogger(__name__)

# Create state machine schema
graph = StateGraph(AgentState)

# Add nodes to the graph
graph.add_node("select_tool", select_tool)
graph.add_node("spec_search", spec_search)
graph.add_node("web_analyze", web_analyze)
graph.add_node("llm_answer", llm_answer)
graph.add_node("manage", manage)
graph.add_node("beauty_output_text", beauty_output_text)
graph.add_node("beauty_output_web", beauty_output_web)

# Set entry point
graph.set_entry_point("select_tool")

# Add conditional edges for dynamic routing
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

graph.add_conditional_edges(
    "web_analyze",
    lambda state: state["next_node"]
)

# Add terminal edges
graph.add_edge("manage", END)
graph.add_edge("beauty_output_text", END)
graph.add_edge("beauty_output_web", END)

# Compile the graph with checkpointing
checkpointer = get_checkpointer()
app = graph.compile(checkpointer=checkpointer)