# from langchain.tools import tool
# from .bdm_chat import process_bdm_query
# # from .bdm_chart import process_bdm_chart_query

# @tool("get_manage_data", return_direct=True)
# def get_manage_data(query: str) -> dict:
#     """
#     Handles BDM-related data queries, including reports and updates for specific time periods.
    
#     This function processes queries to retrieve sales or business data for a specific BDM
#     within a given time frame (e.g., this week, current quarter, this year).
    
#     Examples of supported queries:
#     - "Show John.Doe's weekly report"
#     - "Monthly update for jane.smith"
#     - "Quarterly performance for bob.lee"
#     - "This year's summary for alice.wong"
    
#     Args:
#         query (str): User's query string, which may include:
#                     - BDM name (e.g., "john.doe", "jane.smith")
#                     - Time period (e.g., "this week", "monthly", "quarterly", "this year")
#                     - Type of report (e.g., "report", "update", "summary")
        
#     Returns:
#         dict: A dictionary containing the query results, typically including:
#               - BDM performance metrics
#               - Time-period specific data
#               - Any relevant business intelligence
#     """
#     try:
#         response = process_bdm_query(query)
#         print(f'test:{response}')
#         return response
#     except Exception as e:
#         return {"error": str(e)}
# from langchain.tools import tool
# import json
# from .bdm_chat import process_bdm_query
# from .bdm_chart import get_bdm_chart_response

# def is_chart_query(query: str) -> bool:
#     """判斷是否為圖表查詢"""
#     query_lower = query.lower()
    
#     # 圖表相關的關鍵字
#     chart_keywords = [
#         'graph', 'chart', 'plot', 'diagram', 'figure'
#     ]
    
#     has_chart_keyword = any(keyword in query_lower for keyword in chart_keywords)
    
    
#     return has_chart_keyword or (any(keyword in query_lower for keyword in chart_keywords))

# @tool("get_manage_data", return_direct=True)
# def get_manage_data(query: str) -> dict:
#     """
#     Handles BDM-related data queries, including reports, updates, and charts for specific time periods.
    
#     This function processes queries to:
#     1. Retrieve sales or business data for a specific BDM within a given time frame
#     2. Generate charts for BDM data visualization
    
#     Examples of supported queries:
#     - "Show John.Doe's weekly report"
#     - "Monthly update for jane.smith"
#     - "Quarterly performance for bob.lee"
#     - "This year's summary for alice.wong"
#     - "Show me gary.yccheng's chart for this month"
#     - "Generate a quarterly chart for alice.wang"
    
#     Args:
#         query (str): User's query string, which may include:
#                     - BDM name (e.g., "john.doe", "jane.smith")
#                     - Time period (e.g., "this week", "monthly", "quarterly", "this year")
#                     - Type of report (e.g., "report", "update", "summary", "chart")
        
#     Returns:
#         dict: A dictionary containing:
#               - For data queries: BDM performance metrics and time-period specific data
#               - For chart requests: A JSON string with chart data and metadata
#     """
#     try:
#         if is_chart_query(query):
#             # 處理圖表請求
#             chart_result = get_bdm_chart_response(query)
#             if chart_result.get("success") and "chart_data" in chart_result:
#                 # 將圖表數據轉換為 base64 編碼
#                 import base64
#                 chart_base64 = base64.b64encode(chart_result["chart_data"]).decode('utf-8')
                
#                 # 返回結構化的 JSON 字符串
#                 response = {
#                     "type": "chart",
#                     # "message": chart_result.get("response", "圖表已生成"),
#                     "chart_data": f"data:{chart_result.get('content_type', 'image/png')};base64,{chart_base64}",
#                     "content_type": chart_result.get("content_type", "image/png")
#                 }
#                 return {"response": json.dumps(response)}
#             else:
#                 error_msg = chart_result.get('error', '無法生成圖表')
#                 return {"response": f"圖表生成失敗: {error_msg}"}
#         else:
#             # 原有的 BDM 數據查詢邏輯
#             response = process_bdm_query(query)
#             print(f'test:{response}')
#             return response
#     except Exception as e:
#         return {"response": f"處理請求時出錯: {str(e)}"}
# from langchain.tools import tool
# import json
# from .bdm_chat import process_bdm_query
# from .bdm_chart import get_bdm_chart_response

# def is_chart_query(query: str) -> bool:
#     """判斷是否為圖表查詢"""
#     query_lower = query.lower()
    
#     # 圖表相關的關鍵字
#     chart_keywords = [
#         'graph', 'chart', 'plot', 'diagram', 'figure'
#     ]
    
#     # 檢查查詢中是否包含任何圖表相關的關鍵字
#     has_chart_keyword = any(keyword in query_lower for keyword in chart_keywords)
    
    
#     return has_chart_keyword or (is_show_me_query and any(keyword in query_lower for keyword in chart_keywords))

# @tool("get_manage_data", return_direct=True)
# def get_manage_data(query: str) -> dict:
#     """
#     Handles BDM-related data queries, including reports, updates, and charts for specific time periods.
    
#     This function processes queries to:
#     1. Retrieve sales or business data for a specific BDM within a given time frame
#     2. Generate charts for BDM data visualization
    
#     Examples of supported queries:
#     - "Show John.Doe's weekly report"
#     - "Monthly update for jane.smith"
#     - "Quarterly performance for bob.lee"
#     - "This year's summary for alice.wong"
#     - "Show me gary.yccheng's chart for this month"
#     - "Generate a quarterly chart for alice.wang"
    
#     Args:
#         query (str): User's query string, which may include:
#                     - BDM name (e.g., "john.doe", "jane.smith")
#                     - Time period (e.g., "this week", "monthly", "quarterly", "this year")
#                     - Type of report (e.g., "report", "update", "summary", "chart")
        
#     Returns:
#         dict: A dictionary containing:
#               - For data queries: BDM performance metrics and time-period specific data
#               - For chart requests: A JSON string with chart data and metadata
#     """
#     try:
#         if is_chart_query(query):
#             # 處理圖表請求
#             chart_result = get_bdm_chart_response(query)
#             if chart_result.get("success") and "chart_data" in chart_result:
#                 # 將圖表數據轉換為 base64 編碼
#                 import base64
#                 chart_base64 = base64.b64encode(chart_result["chart_data"]).decode('utf-8')
                
#                 # 返回結構化的 JSON 字符串
#                 response = {
#                     "type": "chart",
#                     # "message": chart_result.get("response", "圖表已生成"),
#                     "chart_data": f"data:{chart_result.get('content_type', 'image/png')};base64,{chart_base64}",
#                     "content_type": chart_result.get("content_type", "image/png")
#                 }
#                 return {"response": json.dumps(response)}
#             else:
#                 error_msg = chart_result.get('error', '無法生成圖表')
#                 return {"response": f"圖表生成失敗: {error_msg}"}
#         else:
#             # 原有的 BDM 數據查詢邏輯
#             response = process_bdm_query(query)
#             print(f'test:{response}')
#             return response
#     except Exception as e:
#         return {"response": f"處理請求時出錯: {str(e)}"}
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