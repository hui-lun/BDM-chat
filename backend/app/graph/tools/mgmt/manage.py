from dataclasses import dataclass
from typing import Dict, Any, Optional
import base64
import json
from langchain.tools import tool
from .bdm_chat import process_bdm_query
from .bdm_chart import get_bdm_chart_response

# Constants
CHART_KEYWORDS = ['graph', 'chart', 'plot', 'diagram', 'figure']

@dataclass
class ChartResponse:
    """Data class for chart responses"""
    chart_data: bytes
    content_type: str = "image/png"
    message: str = "Chart generated successfully"

    def to_dict(self) -> Dict[str, Any]:
        """Convert chart data to dictionary format"""
        chart_base64 = base64.b64encode(self.chart_data).decode('utf-8')
        return {
            "type": "chart",
            "chart_data": f"data:{self.content_type};base64,{chart_base64}",
            "content_type": self.content_type
        }

def is_chart_query(query: str) -> bool:
    """
    Check if the query is related to chart generation
    
    Args:
        query: User's input query string
        
    Returns:
        bool: True if the query contains chart-related keywords, False otherwise
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in CHART_KEYWORDS)

def handle_chart_response(chart_result: Dict[str, Any]) -> Dict[str, str]:
    """
    Process chart generation response
    
    Args:
        chart_result: Dictionary containing chart generation result
        
    Returns:
        Dict: Response containing chart data or error message
    """
    if not chart_result.get("success") or "chart_data" not in chart_result:
        error_msg = chart_result.get('error', 'Failed to generate chart')
        return {"response": f"Chart generation failed: {error_msg}"}
    
    try:
        chart_response = ChartResponse(
            chart_data=chart_result["chart_data"],
            content_type=chart_result.get("content_type", "image/png"),
            message=chart_result.get("response", "Chart generated successfully")
        )
        return {"response": json.dumps(chart_response.to_dict())}
    except Exception as e:
        return {"response": f"Error processing chart data: {str(e)}"}

@tool("get_manage_data", return_direct=True)
def get_manage_data(query: str) -> Dict[str, str]:
    """
    Handle BDM-related data queries including chart generation
    
    This function processes:
    1. Chart generation requests
    2. General BDM data queries
    
    Args:
        query: User's query string
        
    Returns:
        Dict: Response containing requested data or error message
    """
    try:
        if is_chart_query(query):
            chart_result = get_bdm_chart_response(query)
            return handle_chart_response(chart_result)
            
        # Handle non-chart queries
        response = process_bdm_query(query)
        if isinstance(response, dict) and "response" in response:
            return response
        return {"response": str(response)}
        
    except Exception as e:
        return {"response": f"Error processing request: {str(e)}"}