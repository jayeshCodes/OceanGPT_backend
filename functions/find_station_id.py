from typing import Dict, Optional
import pandas as pd


def find_station_id(location: str, station_info: pd.DataFrame) -> Optional[str]:
    """
    Find station ID from a location name using fuzzy matching.

    Args:
        location (str): Location name or partial name
        station_info (pd.DataFrame): DataFrame containing station information

    Returns:
        Optional[str]: Station ID if found, None otherwise
    """
    # Convert to lowercase for matching
    location = location.lower()
    station_info['name_lower'] = station_info['name'].str.lower()

    # Try exact match first
    exact_match = station_info[station_info['name_lower'] == location]
    if not exact_match.empty:
        return exact_match.iloc[0]['station_id']

    # Try partial match
    partial_matches = station_info[station_info['name_lower'].str.contains(location, na=False)]
    if not partial_matches.empty:
        return partial_matches.iloc[0]['station_id']

    # Try matching state
    state_matches = station_info[station_info['state'].str.lower() == location]
    if not state_matches.empty:
        return state_matches.iloc[0]['station_id']

    return None
