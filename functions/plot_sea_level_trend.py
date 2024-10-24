import pandas as pd
from flask import session
import os
from datetime import datetime
import logging


def plot_sea_level_trend(file_path, x_column, y_column, start_year=None, end_year=None):
    logging.info("Plotting sea level trend called")

    if not file_path:
        logging.error("File path is missing")
        return {"response": ["No file has been uploaded. Please upload a CSV file first."], "data": None}

    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"response": ["The uploaded file could not be found. Please upload the file again."], "data": None}

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        return {"response": ["Error reading the CSV file. Please ensure it's a valid sea level data file."],
                "data": None}

    if x_column not in df.columns or y_column not in df.columns:
        return {
            "response": [f"One or both of the specified columns ({x_column}, {y_column}) are not in the dataset."],
            "data": {"xAxis": [], "series": []}
        }

    # Convert x_column to datetime if it's not already
    if df[x_column].dtype != 'datetime64[ns]':
        df[x_column] = pd.to_datetime(df[x_column], errors='coerce')

    # Filter data based on start_year and end_year if provided
    if start_year is not None and end_year is not None:
        start_year = int(start_year)
        end_year = int(end_year)
        df = df[(df[x_column].dt.year >= start_year) & (df[x_column].dt.year <= end_year)]

    # Check if any data remains after filtering
    if df.empty:
        return {
            "response": ["No data available for the specified year range."],
            "data": {"xAxis": [], "series": []}
        }

    # Sort the dataframe by x_column to ensure proper ordering
    df = df.sort_values(by=x_column)

    x_data = df[x_column].dt.strftime('%Y-%m-%d').tolist()  # Convert to string format
    y_data = df[y_column].tolist()

    return {
        "response": [f"Data prepared for plotting {y_column} vs {x_column}" +
                     (f" from {start_year} to {end_year}" if start_year is not None and end_year is not None else "")],
        "data": {
            "xAxis": [{"data": x_data}],
            "series": [{"data": y_data, "name": y_column}]
        }
    }