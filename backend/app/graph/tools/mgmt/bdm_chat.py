import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .enums import process_item, PeriodType, PERIOD_MAPPING
from dateutil.relativedelta import relativedelta
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BDM_API_BASE = "http://192.168.1.166:8000"

# Field order for response
RESPONSE_FIELDS = [
    'Title', 'Weekly update', 'Server Used', 'End user', 'BDM_Name',
    'Status', 'Country', 'Customer Type', 'Industry', 'Estimated Revenue',
    'Importance', 'Summary', 'create date', 'update date', 'region',
    'Company Name'
]

@dataclass
class BDMQueryResponse:
    """Data class for BDM query responses"""
    success: bool
    data: Union[list, dict, None]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format"""
        return {
            'success': self.success,
            **({'error': self.error} if self.error else {}),
            **({'data': self.data} if self.data is not None else {})
        }

def extract_bdm_name(query: str) -> Optional[str]:
    """
    Extract BDM name from query string
    
    Args:
        query: User's input query
        
    Returns:
        str: Extracted BDM name in correct format (with Chinese name if available)
    """
    BDM_NORMALIZATION = {
        'jo.wang': 'Jo.Wang (王俞喬)',
        'jo': 'Jo.Wang (王俞喬)',
    }
    
    # 尝试匹配完整格式 (Name (Chinese))
    if match := re.search(r'[\s:]([A-Za-z]+\.[A-Za-z]+\s*\([^)]+\))', query):
        bdm_name = match.group(1).strip()
        normalized = re.sub(r'\s*\(\s*', ' (', bdm_name)
        normalized = re.sub(r'\s*\)', ')', normalized)
        bdm_key = normalized.split(' ')[0].lower()
        return BDM_NORMALIZATION.get(bdm_key, normalized)
    
    # 尝试匹配简单格式
    excluded_terms = {
        'week', 'month', 'quarter', 'year', 'data', 'report', 'for', 'about', 
        'show', 'get', 'me', 'the', 'and', 'chart', 'graph', 'of', 'in', 'on'
    }
    
    for pattern in [r'[\s:]([A-Za-z]+\.[A-Za-z]+)', r'[\s:]([A-Za-z]{2,})']:
        if match := re.search(pattern, query, re.IGNORECASE):
            bdm_name = match.group(1).strip().lower()
            if bdm_name not in excluded_terms:
                return BDM_NORMALIZATION.get(bdm_name, bdm_name)
    
    return None

def extract_period(query: str) -> PeriodType:
    """
    Extract period type from query
    
    Args:
        query: User's input query
        
    Returns:
        PeriodType: Extracted period type or default to WEEK
    """
    query_lower = query.lower()
    return next((period for period_key, period in PERIOD_MAPPING.items() 
                if period_key in query_lower), PeriodType.WEEK)

def process_bdm_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw BDM API response data
    
    Args:
        data: Raw data from BDM API
        
    Returns:
        List of processed data items
    """
    if not data or not isinstance(data, list):
        return []

    processed_data = []
    for item in filter(None, data):
        try:
            # Process each field
            processed_item = {
                field: "" if field == 'BDM_Name' else item.get(field)
                for field in RESPONSE_FIELDS
                if field in item
            }
            
            # Convert enum values and sort weekly updates
            processed_item = process_item(processed_item, to_text=True)
            if weekly_updates := processed_item.get('Weekly update', []):
                if isinstance(weekly_updates, list):
                    weekly_updates.sort(key=lambda x: int(m.group(1)) if (m := re.search(r'W(\d+)', x or '')) else 0)
                    processed_item['Weekly update'] = weekly_updates
                    
            processed_data.append(processed_item)
            
        except Exception as e:
            logger.warning(f"Error processing BDM data item: {e}")
            continue
            
    return processed_data

def fetch_bdm_data(bdm_name: str, period_type: str) -> Dict[str, Any]:
    """
    Fetch BDM data from API
    
    Args:
        bdm_name: BDM username
        period_type: Time period type (month/quarter/year)
        
    Returns:
        Dict containing API response data
    """
    url = f"{BDM_API_BASE}/mgmt-projects-bdm-time/"
    current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    month_ago = (datetime.now() - relativedelta(months=1)).strftime('%Y-%m-%dT%H:%M:%S')

    params = {
        'bdm_name': bdm_name,
        'time_range': period_type,
        'current_time': current_date if bdm_name == "Jo.Wang (王俞喬)" or period_type == 'week' else month_ago
    }

    try:
        logger.info(f"Fetching BDM data from {url} with params: {params}")
        response = requests.get(url, params=params, timeout=40)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching BDM data: {e}")
        raise

def process_bdm_query(query: str) -> Any:
    """
    Process BDM query and return formatted response
    
    Args:
        query: User's query string
        
    Returns:
        Processed response data or error message
    """
    try:
        if not (bdm_name := extract_bdm_name(query)):
            return {
                "response": "Please provide a valid BDM name. Examples:\n"
                          "- Show data for gary.yccheng this month\n"
                          "- Get weekly report for alice.wang\n"
                          "- bdm: bob.li quarter"
            }
            
        period_type = extract_period(query).value
        return fetch_bdm_data(bdm_name, period_type)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def get_bdm_response(query: str) -> Dict[str, str]:
    """
    Process BDM query and return a formatted response dictionary.
    
    Args:
        query: User's query string
        
    Returns:
        Dict with 'response' key containing JSON string
    """
    try:
        result = process_bdm_query(query)
        return {
            "response": json.dumps(
                result if isinstance(result, (list, dict)) else [str(result)],
                ensure_ascii=False,
                indent=2
            )
        }
    except Exception as e:
        logger.error(f"Error processing BDM response: {e}")
        return {"response": json.dumps([], ensure_ascii=False)}