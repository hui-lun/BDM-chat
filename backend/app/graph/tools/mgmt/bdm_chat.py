# import re
# import requests
# import json
# from datetime import datetime
# from typing import Dict, Any, List
# from .enums import process_item

# # BDM API 端點配置
# BDM_API_BASE = "http://192.168.1.167:8000"

# def get_bdm_response(query: str) -> Dict[str, str]:
#     """
#     Process BDM query and return a formatted response dictionary.
#     The response will always have a 'response' key with JSON string value.
#     """
#     try:
#         result = process_bdm_query(query)
        
#         # 處理回傳結果
#         if isinstance(result, list):
#             # 如果是列表，直接包裝成 response
#             response_data = json.dumps(result, ensure_ascii=False, indent=2)
#         elif isinstance(result, dict):
#             # 如果是單個字典，轉換為列表
#             response_data = json.dumps([result], ensure_ascii=False, indent=2)
#         else:
#             # 其他情況返回空列表
#             response_data = json.dumps([], ensure_ascii=False, indent=2)
            
#         return {"response": response_data}
            
#     except Exception as e:
#         error_msg = f"處理請求時發生未預期的錯誤: {str(e)}"
#         print(error_msg)
#         return {"response": json.dumps([], ensure_ascii=False)}


# def process_bdm_query(query: str) -> Any:
#     # print("\n===== 處理 BDM 查詢 =====")
#     # print(f"查詢內容: {query}")
    
#     try:
#         query = query.lower().strip()
        
#         # 定義時間範圍關鍵詞映射
#         period_map = {
#             'this month': 'month',
#             'monthly': 'month',
#             'month': 'month',
#             'this quarter': 'quarter',
#             'quarterly': 'quarter',
#             'quarter': 'quarter',
#             'this year': 'year',
#             'yearly': 'year',
#             'year': 'year',
#             'all': 'all'
#         }
        
#         # 首先嘗試匹配 BDM 名稱 (格式為 username 或 firstname.lastname)
#         bdm_patterns = [
#             r'[\s:]([a-z]+\.[a-z]+)',  # firstname.lastname
#             r'[\s:]([a-z]{3,})'         # username
#         ]
        
#         bdm_name = None
#         for pattern in bdm_patterns:
#             match = re.search(pattern, query, re.IGNORECASE)
#             if match:
#                 bdm_name = match.group(1).strip()
#                 if bdm_name not in ['week', 'month', 'quarter', 'year', 'data', 'report', 'for', 'about']:
#                     break
#                 bdm_name = None
        
#         # 提取時間範圍
#         period_type = 'month'  # 默認本月
#         for key, value in period_map.items():
#             if key in query:
#                 period_type = value
#                 break
        
#         if not bdm_name:
#             error_msg = "Please provide a BDM name to query. Examples:\n" \
#                       "- Show data for gary.yccheng this month\n" \
#                       "- Get weekly report for alice.wang\n" \
#                       "- bdm: bob.li quarter"
#             # print("Error: No valid BDM name found")
#             return {"response": error_msg}
        
#         # print(f"Extracted BDM name: {bdm_name}, Time period: {period_type}")
        
#         # 構建 BDM API URL 和參數
#         bdm_url = f"{BDM_API_BASE}/bdm/updates/"
#         params = {
#             'bdm': bdm_name,
#             'period_type': period_type,
#             'start_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
#         }
        
#         print(f"調用 BDM API: {bdm_url}")
#         print(f"請求參數: {params}")
        
#         # 發送 GET 請求到 BDM API
#         headers = {
#             'User-Agent': 'Mozilla/5.0',
#             'Accept': 'application/json'
#         }
        
#         print(f"發送 GET 請求到: {bdm_url} 參數: {params}")
#         response = requests.get(
#             bdm_url, 
#             params=params,
#             headers=headers, 
#             timeout=30  # 增加超時時間
#         )
        
#         print(f"響應狀態碼: {response.status_code}")
#         print(f"響應頭: {dict(response.headers)}")
#         print(f"響應內容 (前500字節): {response.text}")
        
#         response.raise_for_status()
        
#         # 返回響應數據
#         try:
#             # 嘗試解析 JSON 響應
#             json_response = response.json()
#             print(f"原始 API 響應: {json.dumps(json_response, ensure_ascii=False, indent=2)}...")
            
#             # 確保 data 存在且是列表
#             if 'data' in json_response and isinstance(json_response['data'], list):
#                 # 過濾掉空項目
#                 filtered_data = [item for item in json_response['data'] if item]
#                 print(f"過濾後的數據條數: {len(filtered_data)}")
                
#                 # 定義需要保留的欄位及其順序
#                 field_order = [
#                     'Title', 'Weekly update', 'Server Used', 'End user', 'BDM_Name',
#                     'Status', 'Country', 'Customer Type', 'Industry', 'Estimated Revenue',
#                     'Importance', 'Summary', 'create date', 'update date', 'region',
#                     'Company Name'
#                 ]
                
#                 # 處理每個項目
#                 processed_data = []
#                 for item in filtered_data:
#                     try:
#                         # 創建新項目，按照指定順序添加欄位
#                         new_item = {}
                        
#                         # 處理每個欄位
#                         for field in field_order:
#                             if field in item:
#                                 value = item[field]
                                
#                                 # 特殊處理特定欄位
#                                 if field == 'BDM_Name':
#                                     new_item[field] = ""  # BDM_Name 設為空字串
#                                 else:
#                                     new_item[field] = value
                        
#                         # 轉換枚舉值為文字描述
#                         new_item = process_item(new_item, to_text=True)
                        
#                         # 處理 Weekly update 排序
#                         if 'Weekly update' in new_item and isinstance(new_item['Weekly update'], list):
#                             # 使用正則表達式提取週數進行排序
#                             def get_week_num(update):
#                                 match = re.search(r'W(\d+)', update)
#                                 return int(match.group(1)) if match else 0
                            
#                             # 按照週數升序排序（從舊到新）
#                             new_item['Weekly update'].sort(key=get_week_num)
                        
#                         processed_data.append(new_item)
                        
#                     except Exception as e:
#                         # print(f"處理項目時發生錯誤: {str(e)}")
#                         continue
                
#                 # 確保至少有一筆資料
#                 if not processed_data:
#                     return []
                
#                 # 直接回傳處理後的資料
#                 return processed_data[0] if len(processed_data) == 1 else processed_data
                
#             else:
#                 return []
                
#         except json.JSONDecodeError as e:
#             # print(f"解析 BDM API 回應時發生錯誤: {str(e)}")
#             return []
            
#     except requests.exceptions.RequestException as e:
#         # print(f"請求 BDM API 時發生錯誤: {str(e)}")
#         return []
        
#     except Exception as e:
#         # print(f"處理 BDM 查詢時發生未預期的錯誤: {str(e)}")
#         return []

import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .enums import process_item
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BDM_API_BASE = "http://192.168.1.167:8000"
API_TIMEOUT = 40  # seconds

# Constants
PERIOD_MAPPING = {
    'this month': 'month',
    'monthly': 'month',
    'month': 'month',
    'this quarter': 'quarter',
    'quarterly': 'quarter',
    'quarter': 'quarter',
    'this year': 'year',
    'yearly': 'year',
    'year': 'year',
    'all': 'all'
}

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
        response = {'success': self.success}
        if self.error:
            response['error'] = self.error
        if self.data is not None:
            response['data'] = self.data
        return response

def extract_bdm_name(query: str) -> Optional[str]:
    """
    Extract BDM name from query string
    
    Args:
        query: User's input query
        
    Returns:
        str: Extracted BDM name or None if not found
    """
    bdm_patterns = [
        r'[\s:]([a-z]+\.[a-z]+)',  # firstname.lastname
        r'[\s:]([a-z]{3,})'         # username
    ]
    
    excluded_terms = {'week', 'month', 'quarter', 'year', 'data', 'report', 'for', 'about'}
    
    for pattern in bdm_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            bdm_name = match.group(1).strip().lower()
            if bdm_name not in excluded_terms:
                return bdm_name
    return None

def extract_period(query: str) -> str:
    """
    Extract time period from query string
    
    Args:
        query: User's input query
        
    Returns:
        str: Extracted period type (default: 'month')
    """
    for key, value in PERIOD_MAPPING.items():
        if key in query.lower():
            return value
    return 'month'  # Default period

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
    for item in filter(None, data):  # Filter out None/empty items
        try:
            # Process each field
            processed_item = {
                field: "" if field == 'BDM_Name' else item.get(field)
                for field in RESPONSE_FIELDS
                if field in item
            }
            
            # Convert enum values to text
            processed_item = process_item(processed_item, to_text=True)
            
            # Sort weekly updates
            weekly_updates = processed_item.get('Weekly update', [])
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
    url = f"{BDM_API_BASE}/bdm/updates/"
    params = {
        'bdm': bdm_name,
        'period_type': period_type,
        'start_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    }
    
    try:
        logger.info(f"Fetching BDM data from {url} with params: {params}")
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
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
        query = query.lower().strip()
        bdm_name = extract_bdm_name(query)
        
        if not bdm_name:
            return {
                "response": "Please provide a valid BDM name. Examples:\n"
                          "- Show data for gary.yccheng this month\n"
                          "- Get weekly report for alice.wang\n"
                          "- bdm: bob.li quarter"
            }
            
        period_type = extract_period(query)
        api_response = fetch_bdm_data(bdm_name, period_type)
        
        if not api_response or 'data' not in api_response:
            return []
            
        processed_data = process_bdm_data(api_response['data'])
        return processed_data[0] if len(processed_data) == 1 else processed_data
        
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
        response_data = json.dumps(
            result if isinstance(result, (list, dict)) else [str(result)],
            ensure_ascii=False,
            indent=2
        )
        return {"response": response_data}
    except Exception as e:
        logger.error(f"Error processing BDM response: {e}")
        return {"response": json.dumps([], ensure_ascii=False)}