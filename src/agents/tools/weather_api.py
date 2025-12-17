"""
Weather API Tool - Location detection and IMD station mapping
Uses LangChain @tool decorator for LangGraph compatibility
"""

from langchain.tools import tool
from typing import Optional

from agents.tools.imd_scraper import imd_scraper

# IMD Station ID mapping
STATION_MAP = {
    "bhubaneswar": 42971,
    "cuttack": 42963,
    "puri": 43053,
    "sambalpur": 42823,
    "balasore": 43185,
    "berhampur": 43279,
    "rourkela": 42793,
    "kendrapara": 93261,
    "khordha": 88834,
    "jagatsinghpur": 93260,
    "paradip": 42976,
    "bhadrak": 43183,
    "angul": 42841,
    "dhenkanal": 42891,
    "jajpur": 93259
}


@tool
def weather_location_detector(query: str) -> str:
    """
    Detect location from user weather query.
    
    Extracts city/district name from natural language queries.
    Defaults to Bhubaneswar if no location found.
    
    Args:
        query: User's weather query
        
    Returns:
        Detected location name (lowercase)
        
    Examples:
        weather_location_detector("weather in puri") -> "puri"
        weather_location_detector("will it rain today") -> "bhubaneswar"
    """
    query_lower = query.lower()
    
    # Check for each known location
    for city in STATION_MAP.keys():
        if city in query_lower:
            return city
    
    # Default to capital city
    return "bhubaneswar"


@tool
def weather_station_mapper(location: str) -> Optional[int]:
    """
    Get IMD station ID for a given location.
    
    Maps Odisha city/district names to their IMD station IDs
    for weather data retrieval.
    
    Args:
        location: Location name (case-insensitive)
        
    Returns:
        IMD station ID (integer) or None if not found
        
    Examples:
        weather_station_mapper("bhubaneswar") -> 42971
        weather_station_mapper("puri") -> 43053
    """
    location_lower = location.lower().strip()
    return STATION_MAP.get(location_lower)


@tool
def get_all_weather_locations() -> str:
    """
    Get list of all supported weather locations.
    
    Returns:
        Comma-separated string of available locations
    """
    locations = sorted(STATION_MAP.keys())
    return ", ".join(locations)

@tool
def imd_weather_fetcher(station_id: int) -> str:
    """
    Fetch structured weather data from IMD using Selenium scraper.
    
    Args:
        station_id: IMD station ID (integer)

    Returns:
        JSON string result from the scraper
    """
    return imd_scraper({"station_id": station_id})