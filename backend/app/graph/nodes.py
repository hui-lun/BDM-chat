import json
import logging
from typing_extensions import TypedDict
from .llm import llm
from .tools.spec.spec_analyze import search_database
from .tools.web.web_analyze import fetch_and_analyze_web_html
from .tools.mgmt.manage import get_manage_data
from .tools.mgmt.pretty_output import pretty_print_projects

# Configure logging
logger = logging.getLogger(__name__)

# State structure
class AgentState(TypedDict):
    agent_query: str
    summary: str
    next_node: str
    needs_streaming: bool

# Node definitions
def select_tool(state: AgentState):
    """Determine which tool to use based on the user query"""
    query = state["agent_query"]
    logger.info("[select_tool] Determining tool selection")
    
    prompt = (
        f"Given the user input:'{query}', decide which tool to use:\n"
        "1. If the question is about retrieving data from the database or from qvl(QVL), return 'spec_search'.\n"
        "2. If the question requires analyzing web content, return 'web_analyze'.\n"
        "3. If the question is about BDM reports, updates, or contains a person's name (e.g., gary.yccheng, alice.wang) "
        "and/or time period (e.g., this week, monthly, quarterly, this year), return 'manage'.\n"
        "ONLY return the exact tool name without explanation."
    )
    
    predicted_label = llm.invoke(prompt).content.strip().lower()
    logger.info(f"[select_tool] Selected tool: {predicted_label}")
    return {"next_node": predicted_label}

def spec_search(state: AgentState):
    """Search for specifications in the database"""
    logger.info("[spec_search] Executing spec search")
    logger.debug(f"Query: {state['agent_query']}")
    
    summary, temp = search_database(state["agent_query"])
    if summary == "database not found this server":
        logger.info("[spec_search] No database found, redirecting to web_analyze")
        return {
            "next_node": "web_analyze"
        }
    else:
        logger.info(f"[spec_search] Found summary: {summary}")

        if temp=="qvl":
            return {
                "summary": summary,
                # "next_node": "beauty_output_text"
                "next_node": "END"
            }
        else:
            return {
                "summary": summary,
                "next_node": "beauty_output_text"
                # "next_node": "END"
            }

def web_analyze(state: AgentState):
    """Analyze web content based on the query"""
    logger.info("[web_analyze] Processing web analysis request")
    result = fetch_and_analyze_web_html.invoke(state["agent_query"])
    logger.info(f"[web_analyze] Analysis result: {result}")
    return {
        "summary": result.get("summary", ""),
        "next_node": "beauty_output_web"
    }

def manage(state: AgentState):
    """Process BDM management requests"""
    logger.info("[manage] Processing BDM management request")
    query = state["agent_query"]
    logger.debug(f"[manage] Query: {query}")
    
    try:
        # Get the raw result from get_manage_data
        result = get_manage_data.invoke(query)
        
        # Convert the result to a string that can be displayed in the frontend
        if isinstance(result, dict) and 'response' in result:
            logger.debug("[manage] Processing response with 'response' field")
            response_text = result['response']
            data = response_text
            temp_node = "END"            
            
            if not ('"type": "chart"' in str(response_text)):
                logger.debug("[manage] Formatting non-chart response")
                response_text = pretty_print_projects(data)
                temp_node = "beauty_output_text"
            
            logger.debug("[manage] Successfully processed BDM query")

        else:
            logger.debug("[manage] Converting result to JSON and formatting")
            response_text = json.dumps(result, ensure_ascii=False, indent=2)
            data = json.loads(response_text)
            response_text = pretty_print_projects(data)
            logger.debug("[manage] Successfully processed BDM query")
        
        logger.info(f"[manage] Sending response to frontend: {response_text[:100]}...")
        
        return {
            "summary": response_text,
            "next_node": temp_node
        }
        
    except Exception as e:
        error_msg = f"Error processing BDM query: {str(e)}"
        logger.error(f"[manage] {error_msg}")
        return {
            "next_node": "llm_answer"
        }

def llm_answer(state: AgentState):
    """Process requests using LLM directly"""
    logger.info("[llm_answer] Processing LLM request")
    response = llm.invoke(state["agent_query"])
    logger.debug(f"[llm_answer] LLM response: {response}")
    return {
        "summary": response.content,
        "next_node": "END"
    }

def beauty_output_text(state: AgentState):
    """Generate formatted markdown response for text content"""
    logger.info("[beauty_output_text] Generating response with markdown format for text content")

    prompt = (
    "You are a professional technical writer.\n"
    "Please return the response in **Markdown format**, but do NOT wrap it in triple backticks (```) or use ```markdown.\n"
    "Just return plain Markdown content directly.\n"
    "You may rephrase or expand slightly for clarity, but DO NOT invent or fabricate any data.\n"
    "Do NOT add placeholders like '[Please Replace]'.\n"
    "IMPORTANT: You MUST use proper Markdown syntax:\n"
    "- Use ## for level-2 headings\n"
    "- Use **text** for bold text\n"
    "- Use *text* for italic text\n"
    "- Use - or * for bullet points\n"
    "- Use 1. 2. 3. for numbered lists\n"
    "- Leave blank lines between sections\n"
    "- Use `code` for inline code\n"
    "- Use ``` for code blocks\n\n"
    "- For plain URLs, use Markdown link format: [link text](https://example.com)\n\n"
    "Here is the content:\n"
        f"{state['summary']}"
    )

    # Set streaming flag
    state["summary"] = prompt
    state["needs_streaming"] = True
    
    return {
        "summary": prompt,
        "needs_streaming": True
    }

def beauty_output_web(state: AgentState):
    """Generate formatted markdown response for web search results"""
    logger.info("[beauty_output_web] Generating response with markdown format for web search results")

    prompt = (
        "You are a professional technical writer and research analyst. "
        "Based on the following web search results, please provide a comprehensive and well-structured response. "
        "Your response should include:\n"
        "- A level-2 Markdown title (## Web Search Results)\n"
        "- A brief summary of the key findings\n"
        "- Section headers in bold (e.g., **Key Information**, **Important Details**)\n"
        "- Bullet points for important information\n"
        "- Important terms in bold\n"
        "- One blank line between sections for readability\n"
        "- Make the content organized, professional, and easy to read\n"
        "- Only use information that is explicitly present in the search results\n"
        "- If the search results cover multiple topics, focus on the most relevant to the user's question\n"
        "- Summarize the answer in a clear, concise manner\n\n"
        "Here are the web search results:\n"
        f"{state['summary']}"
    )

    # Set streaming flag
    state["summary"] = prompt
    state["needs_streaming"] = True
    
    return {
        "summary": prompt,
        "needs_streaming": True
    }

