import re
import requests
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from .bdm_chat import BDM_API_BASE

# BDM API endpoint configuration
# BDM_API_BASE = "http://192.168.1.167:8000"  # Same base URL as in bdm_chat.py

class PeriodType(str, Enum):
    """Enum for different time period types"""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

def get_bdm_chart(
    bdm_name: str,
    period_type: PeriodType = PeriodType.WEEK,
    start_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Fetch BDM chart data from API
    
    Args:
        bdm_name: Name of the BDM
        period_type: Time period type (default: WEEK)
        start_date: Optional start date for the data
        
    Returns:
        Dictionary containing chart data or error information
    """
    try:
        print(f"[DEBUG] Fetching {period_type.value} chart data for {bdm_name}...")
        
        # Prepare request parameters
        params = {"period_type": period_type.value}
        if start_date:
            params["start_date"] = start_date.isoformat()
        
        # Make API request
        url = f"{BDM_API_BASE}/bdm/status-chart/{bdm_name}"
        print(f"[DEBUG] Request URL: {url}")
        print(f"[DEBUG] Request params: {params}")
        print("[DEBUG] Sending request to BDM API...")
        
        response = requests.get(url, params=params, timeout=30)
        # print("[DEBUG] Sending this")
        response.raise_for_status()
        
        # Check if response contains data
        if not response.content:
            error_msg = "Received empty chart data"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False,
                "response": error_msg,
                "error": error_msg
            }
        
        # Process successful response
        content_type = response.headers.get('content-type', 'image/png')
        print(f"[DEBUG] Successfully retrieved chart data, size: {len(response.content)} bytes, type: {content_type}")
        
        return {
            "success": True,
            "response": f"Successfully retrieved {period_type.value} chart for {bdm_name}",
            "chart_data": response.content,
            "content_type": content_type
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error while requesting BDM chart API: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error while processing BDM chart data: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

def get_bdm_chart_response(query: str) -> Dict[str, Any]:
    """
    Process chart query and return formatted response
    
    Args:
        query: User's query string
        
    Returns:
        Dictionary containing chart data or error message
    """
    print(f'[DEBUG] Processing BDM chart query: {query}')
    
    try:
        # Check if query is related to charts
        query_lower = query.lower()
        chart_keywords = ['graph', 'chart', 'plot', 'diagram', 'figure']
        if not any(keyword in query_lower for keyword in chart_keywords):
            return {
                "success": False,
                "response": "No chart-related query detected",
                "should_skip": True
            }
        
        # Extract BDM name from query
        bdm_match = re.search(
            r'(?:bdm[\s:]*)?([a-z]+\.[a-z]+)|show\s+me\s+([a-z]+\.[a-z]+)', 
            query_lower
        )
        
        # Set default values
        bdm_name = "gary.yccheng"  # Default BDM name
        period_type = PeriodType.WEEK  # Default period type
        
        # Extract BDM name if found
        if bdm_match:
            bdm_name = bdm_match.group(1) or bdm_match.group(2) or bdm_name
        
        # Map period type keywords to PeriodType enum
        period_map = {
            'month': PeriodType.MONTH,
            'quarter': PeriodType.QUARTER,
            'year': PeriodType.YEAR,
            'this month': PeriodType.MONTH,
            'this quarter': PeriodType.QUARTER,
            'this year': PeriodType.YEAR,
            'monthly': PeriodType.MONTH,
            'quarterly': PeriodType.QUARTER,
            'yearly': PeriodType.YEAR
        }
        
        # Find period type in query
        for period_key, period_value in period_map.items():
            if period_key in query_lower:
                period_type = period_value
                break
        
        print(f"Fetching {period_type.value} chart for {bdm_name}...")
        
        # Get chart data
        result = get_bdm_chart(bdm_name, period_type)
        
        if result.get("success") and "chart_data" in result:
            chart_data = result["chart_data"]
            content_type = result.get("content_type", "image/png")
            print(f"[DEBUG] Successfully retrieved chart data, size: {len(chart_data) if chart_data else 0} bytes, type: {content_type}")
            
            # Ensure chart data is not empty
            if not chart_data:
                raise ValueError("Empty chart data")

            return {
                "chart_data": chart_data,
                "content_type": content_type,
                "success": True
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"[ERROR] Failed to retrieve chart: {error_msg}")
            return {
                "error": True,
                "success": False,
                "details": str(error_msg)
            }
            
    except Exception as e:
        error_msg = f"Error while processing BDM chart request: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "response": error_msg,
            "error": True,
            "success": False
        }