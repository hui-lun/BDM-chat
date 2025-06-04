from enum import IntEnum, Enum
from typing import Dict, Any

# Status
class Status(IntEnum):
    INITIAL = 0
    PROPOSAL = 1
    POC = 2
    PROJECT_PAUSE = 3
    PROJECT_WIN = 4
    PROJECT_LOSE = 5
    PROJECT_KICK_OFF = 6
    PROJECT_CLOSE = 7

# Country
class Country(IntEnum):
    US = 0
    CANADA = 1
    ARGENTINA = 2
    BRAZIL = 3
    COLOMBIA = 4
    MEXICO = 5
    JAPAN = 6
    KOREA = 7
    SINGAPORE = 8
    INDIA = 9
    VIETNAM = 10
    INDONESIA = 11
    THAILAND = 12

# Region
class Region(IntEnum):
    US_CANADA = 0
    LATAM = 1
    JP_KR_ANZ = 2
    SEA_INDIA = 3

class PeriodType(str, Enum):
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

# Status Mapping
STATUS_MAPPING = {
    Status.INITIAL: "Initial",
    Status.PROPOSAL: "Proposal",
    Status.POC: "PoC",
    Status.PROJECT_PAUSE: "Project Pause",
    Status.PROJECT_WIN: "Project Win",
    Status.PROJECT_LOSE: "Project Lose",
    Status.PROJECT_KICK_OFF: "Project Kick Off",
    Status.PROJECT_CLOSE: "Project Close"
}

# Country Mapping
COUNTRY_MAPPING = {
    Country.US: "US",
    Country.CANADA: "Canada",
    Country.ARGENTINA: "Argentina",
    Country.BRAZIL: "Brasil",
    Country.COLOMBIA: "Colombia",
    Country.MEXICO: "Mexico",
    Country.JAPAN: "Japan",
    Country.KOREA: "Korea",
    Country.SINGAPORE: "Singapore",
    Country.INDIA: "India",
    Country.VIETNAM: "Vietnam",
    Country.INDONESIA: "Indonesia",
    Country.THAILAND: "Thailand"
}

# Region Mapping
REGION_MAPPING = {
    Region.US_CANADA: "US/Canada",
    Region.LATAM: "LATAM",
    Region.JP_KR_ANZ: "JP/KR/ANZ",
    Region.SEA_INDIA: "SEA/India"
}

PERIOD_MAPPING = {
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

def map_status(status_value: int) -> str:
    try:
        status = Status(status_value)
        return STATUS_MAPPING.get(status, f"Unknown Status ({status_value})")
    except ValueError:
        return f"Invalid Status ({status_value})"

def map_country(country_value: int) -> str:
    try:
        country = Country(country_value)
        return COUNTRY_MAPPING.get(country, f"Unknown Country ({country_value})")
    except ValueError:
        return f"Invalid Country ({country_value})"

def map_region(region_value: int) -> str:
    try:
        region = Region(region_value)
        return REGION_MAPPING.get(region, f"Unknown Region ({region_value})")
    except ValueError:
        return f"Invalid Region ({region_value})"

TEXT_TO_STATUS  = {v.lower(): k for k, v in STATUS_MAPPING.items()}
TEXT_TO_COUNTRY = {v.lower(): k for k, v in COUNTRY_MAPPING.items()}
TEXT_TO_REGION  = {v.lower(): k for k, v in REGION_MAPPING.items()}

def text_to_status(text: str) -> int:
    if not text:
        return 0
    return TEXT_TO_STATUS.get(text.lower().strip(), 0)

def text_to_country(text: str) -> int:
    if not text:
        return 0
    return TEXT_TO_COUNTRY.get(text.lower().strip(), 0)

def text_to_region(text: str) -> int:
    if not text:
        return 0
    return TEXT_TO_REGION.get(text.lower().strip(), 0)

def process_item(item: Dict[str, Any], to_text: bool = True) -> Dict[str, Any]:
    new_item = item.copy()
    
    if to_text:
        if 'Status' in new_item and isinstance(new_item['Status'], int):
            new_item['Status'] = map_status(new_item['Status'])
        
        if 'Country' in new_item and isinstance(new_item['Country'], int):
            new_item['Country'] = map_country(new_item['Country'])
        
        if 'region' in new_item and isinstance(new_item['region'], int):
            new_item['region'] = map_region(new_item['region'])
    else:
        if 'Status' in new_item and isinstance(new_item['Status'], str):
            new_item['Status'] = text_to_status(new_item['Status'])
        
        if 'Country' in new_item and isinstance(new_item['Country'], str):
            new_item['Country'] = text_to_country(new_item['Country'])
        
        if 'region' in new_item and isinstance(new_item['region'], str):
            new_item['region'] = text_to_region(new_item['region'])
    
    if 'Importance' in new_item and isinstance(new_item['Importance'], (int, float)):
        new_item['Importance'] = max(1, min(5, int(new_item['Importance'])))
    
    return new_item
