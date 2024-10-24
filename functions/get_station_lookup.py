import pandas as pd
import requests

def get_station_lookup() -> pd.DataFrame:
    """
    Fetch all water level stations from NOAA's Metadata API and return as a DataFrame.

    Returns:
        pandas.DataFrame: Station information including IDs, names, and locations
    """
    metadata_url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"

    try:
        response = requests.get(metadata_url)
        response.raise_for_status()
        data = response.json()

        # Extract station data
        stations = pd.DataFrame(data['stations'])

        # Filter for active water level stations
        water_level_stations = stations[
            (stations['datums'].notna()) &  # Has datum information
            (stations['portscode'].notna())  # Is a water level station
            ]

        # Create a clean DataFrame with relevant information
        station_info = pd.DataFrame({
            'station_id': water_level_stations['id'],
            'name': water_level_stations['name'],
            'state': water_level_stations['state'],
            'latitude': water_level_stations['lat'],
            'longitude': water_level_stations['lng']
        })

        return station_info

    except requests.RequestException as e:
        print(f"Failed to fetch station data: {str(e)}")
        return pd.DataFrame()
