import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

try:
    from functions.find_station_id import find_station_id
    from functions.get_station_lookup import get_station_lookup
except ImportError:
    import find_station_id
    import get_station_lookup


def save_sea_level_data(location: str) -> str:
    """
    Fetch sea level data for a given location and save it as a CSV file
    in the '../data' directory. If a file for the same station exists and
    is less than 30 days old, skip the download.

    Args:
        location (str): Location name or station ID
    """
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)

    # Get station information
    station_info = get_station_lookup()
    if station_info.empty:
        return "Failed to fetch station information"

    # If input is not a station ID, try to find matching station
    if not location.isdigit() or len(location) != 7:
        station_id = find_station_id(location, station_info)
        if not station_id:
            print(f"Could not find station ID for location: {location}")
            print("Available stations near search term:")
            # Print nearby or similar named stations
            similar_stations = station_info[
                station_info['name'].str.lower().str.contains(location.lower(), na=False)
            ]
            if not similar_stations.empty:
                return similar_stations[['name', 'state', 'station_id']].head()
    else:
        station_id = location

    # Check for existing files for this station
    existing_files = list(data_dir.glob(f"sea_level_{station_id}_*.csv"))

    if existing_files:
        # Get the most recent file
        most_recent_file = max(existing_files, key=lambda x: x.stat().st_mtime)
        file_age = datetime.now() - datetime.fromtimestamp(most_recent_file.stat().st_mtime)

        # If file is less than 30 days old, skip download
        if file_age.days < 30:
            print(f"Using existing file: {most_recent_file}")
            print(f"File age: {file_age.days} days")
            return f"Using existing file f{most_recent_file}"
        else:
            print(f"Existing file is {file_age.days} days old. Downloading new data...")

    # Set up dates for last 24 hours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)

    # Format dates for API
    start_date = start_date.strftime('%Y%m%d %H:%M')
    end_date = end_date.strftime('%Y%m%d %H:%M')

    # Build API URL with parameters
    base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        'station': station_id,
        'product': 'water_level',
        'begin_date': start_date,
        'end_date': end_date,
        'datum': 'MSL',  # Using Mean Sea Level datum
        'units': 'metric',
        'time_zone': 'gmt',
        'format': 'json',
        'application': 'PythonSeaLevelFetcher'
    }

    try:
        # Get data from API
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if 'error' in data:
            raise ValueError(f"API Error: {data['error']['message']}")

        # Convert to DataFrame
        df = pd.DataFrame(data['data'])

        # Add station information
        station_row = station_info[station_info['station_id'] == station_id].iloc[0]
        df['station_name'] = station_row['name']
        df['station_id'] = station_id
        df['latitude'] = station_row['latitude']
        df['longitude'] = station_row['longitude']

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"sea_level_{station_id}_{timestamp}.csv"
        filepath = data_dir / filename

        # Save to CSV
        df.to_csv(filepath, index=False)
        print(f"Data saved to: {filepath}")
        print(f"Station: {station_row['name']} ({station_id})")

        return f"Data saved to: {filepath}\n Station {station_row['name']} ({station_id})]"

    except requests.RequestException as e:
        print(f"Failed to fetch data: {str(e)}")
        return f"Failed to fetch data: {str(e)}"
    except ValueError as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"


if __name__ == "__main__":
    # Example usage:
    # By station ID
    save_sea_level_data('9414290')
    # By location name
    save_sea_level_data('Los Angeles')