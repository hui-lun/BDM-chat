import requests
from .enums import PeriodType, PERIOD_MAPPING
from datetime import datetime
from typing import Dict, Any, Optional
from .bdm_chat import BDM_API_BASE, extract_bdm_name
from dateutil.relativedelta import relativedelta

def get_bdm_chart(bdm_name: str, current_time: Optional[datetime], time_range: PeriodType, chart_type: str) -> Dict[str, Any]:
    """
    Fetch BDM chart data from API
    
    Args:
        bdm_name: Name of the BDM
        current_time: Current time for data filtering
        time_range: Time period type
        chart_type: Type of chart to generate
        
    Returns:
        Dictionary containing chart data or error information
    """
    try:
        # Prepare request parameters
        month_ago = (datetime.now() - relativedelta(months=1)).strftime('%Y-%m-%dT%H:%M:%S')
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        params = {
            'bdm_name': bdm_name,
            'current_time': current_time if bdm_name == "Jo.Wang (王俞喬)" or time_range == 'week' else month_ago,
            "time_range": time_range.value,
            'chart_type': chart_type
        }

        # Make API request
        url = f"{BDM_API_BASE}/mgmt-status-chart-bdm-time"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        if not response.content:
            return {
                "success": False,
                "error": "Received empty chart data"
            }
        
        return {
            "success": True,
            "response": f"Successfully retrieved {time_range.value} chart for {bdm_name}",
            "chart_data": response.content,
            "content_type": response.headers.get('content-type', 'image/png')
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Error while requesting BDM chart API: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error while processing BDM chart data: {str(e)}"
        }

def get_bdm_chart_response(query: str) -> Dict[str, Any]:
    """
    Process chart query and return formatted response
    
    Args:
        query: User's query string
        
    Returns:
        Dictionary containing chart data or error message
    """
    try:
        # Check if query is related to charts
        query_lower = query.lower()
        if not any(keyword in query_lower for keyword in ['graph', 'chart', 'plot', 'diagram', 'figure']):
            return {
                "success": False,
                "response": "No chart-related query detected",
                "should_skip": True
            }

        # Extract BDM name and time range
        bdm_name = extract_bdm_name(query)
        time_range = next((period for period_key, period in PERIOD_MAPPING.items() 
                          if period_key in query_lower), PeriodType.WEEK)
        
        # Get chart data
        result = get_bdm_chart(bdm_name, datetime.now(), time_range, "pie")
       
        if result.get("success") and result.get("chart_data"):
            return {
                "chart_data": result["chart_data"],
                "content_type": result.get("content_type", "image/png"),
                "success": True
            }
            
        return {
            "error": True,
            "success": False,
            "details": result.get('error', 'Unknown error')
        }
            
    except Exception as e:
        return {
            "response": f"Error while processing BDM chart request: {str(e)}",
            "error": True,
            "success": False
        }