from langchain.tools import tool
from .bdm_chat import process_bdm_query
# from .bdm_chart import process_bdm_chart_query

@tool("get_manage_data", return_direct=True)
def get_manage_data(query: str) -> dict:
    """
    Handles BDM-related data queries, including reports and updates for specific time periods.
    
    This function processes queries to retrieve sales or business data for a specific BDM
    within a given time frame (e.g., this week, current quarter, this year).
    
    Examples of supported queries:
    - "Show John.Doe's weekly report"
    - "Monthly update for jane.smith"
    - "Quarterly performance for bob.lee"
    - "This year's summary for alice.wong"
    
    Args:
        query (str): User's query string, which may include:
                    - BDM name (e.g., "john.doe", "jane.smith")
                    - Time period (e.g., "this week", "monthly", "quarterly", "this year")
                    - Type of report (e.g., "report", "update", "summary")
        
    Returns:
        dict: A dictionary containing the query results, typically including:
              - BDM performance metrics
              - Time-period specific data
              - Any relevant business intelligence
    """
    try:
        response = process_bdm_query(query)
        print(f'test:{response}')
        return response
    except Exception as e:
        return {"error": str(e)}
from langchain.tools import tool
import json
from .bdm_chat import process_bdm_query
from .bdm_chart import get_bdm_chart_response

def is_chart_query(query: str) -> bool:
    """判斷是否為圖表查詢"""
    query_lower = query.lower()
    
    # 圖表相關的關鍵字
    chart_keywords = [
        'graph', 'chart', 'plot', 'diagram', 'figure'
    ]
    
    has_chart_keyword = any(keyword in query_lower for keyword in chart_keywords)
    
    
    return has_chart_keyword or (any(keyword in query_lower for keyword in chart_keywords))

@tool("get_manage_data", return_direct=True)
def get_manage_data(query: str) -> dict:
    """
    Handles BDM-related data queries, including reports, updates, and charts for specific time periods.
    
    This function processes queries to:
    1. Retrieve sales or business data for a specific BDM within a given time frame
    2. Generate charts for BDM data visualization
    
    Examples of supported queries:
    - "Show John.Doe's weekly report"
    - "Monthly update for jane.smith"
    - "Quarterly performance for bob.lee"
    - "This year's summary for alice.wong"
    - "Show me gary.yccheng's chart for this month"
    - "Generate a quarterly chart for alice.wang"
    
    Args:
        query (str): User's query string, which may include:
                    - BDM name (e.g., "john.doe", "jane.smith")
                    - Time period (e.g., "this week", "monthly", "quarterly", "this year")
                    - Type of report (e.g., "report", "update", "summary", "chart")
        
    Returns:
        dict: A dictionary containing:
              - For data queries: BDM performance metrics and time-period specific data
              - For chart requests: A JSON string with chart data and metadata
    """
    try:
        if is_chart_query(query):
            # 處理圖表請求
            chart_result = get_bdm_chart_response(query)
            if chart_result.get("success") and "chart_data" in chart_result:
                # 將圖表數據轉換為 base64 編碼
                import base64
                chart_base64 = base64.b64encode(chart_result["chart_data"]).decode('utf-8')
                
                # 返回結構化的 JSON 字符串
                response = {
                    "type": "chart",
                    # "message": chart_result.get("response", "圖表已生成"),
                    "chart_data": f"data:{chart_result.get('content_type', 'image/png')};base64,{chart_base64}",
                    "content_type": chart_result.get("content_type", "image/png")
                }
                return {"response": json.dumps(response)}
            else:
                error_msg = chart_result.get('error', '無法生成圖表')
                return {"response": f"圖表生成失敗: {error_msg}"}
        else:
            # 原有的 BDM 數據查詢邏輯
            response = process_bdm_query(query)
            print(f'test:{response}')
            return response
    except Exception as e:
        return {"response": f"處理請求時出錯: {str(e)}"}
