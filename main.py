import os
import sys

# Ensure the project directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import load_config, load_and_clean_data
from data_processor import process_data
from dashboard import render_dashboard, display_error


def main():

    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")

    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError, Exception) as e:
        display_error(f"Configuration Error: {e}")
        return

    data_file = os.path.join(base_dir, "gdp_with_continent_filled.csv")
    try:
        data = load_and_clean_data(data_file)
    except (FileNotFoundError, ValueError, Exception) as e:
        display_error(f"Data Loading Error: {e}")
        return

    if not data:
        display_error("No valid data rows after cleaning.")
        return


    try:
        results = process_data(data, config)
    except Exception as e:
        display_error(f"Processing Error: {e}")
        return


    try:
        render_dashboard(results)
    except Exception as e:
        display_error(f"Dashboard Rendering Error: {e}")
        return


if __name__ == "__main__":
    main()
