import csv
import json
import os

def load_config(config_path):
    
    #check if config file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, 'r') as file:
        config = json.load(file)
    
    #validate required keys and values
    required_keys = ['region', 'year', 'operation', 'output']
    missing_keys = list(filter(lambda k: k not in config, required_keys))
    if missing_keys:
        raise ValueError(f"Missing required config keys: {missing_keys}")
    valid_operations = ['average', 'sum']
    if config['operation'] not in valid_operations:
        raise ValueError(f"Invalid operation '{config['operation']}'. Must be one of: {valid_operations}")
    valid_outputs = ['dashboard', 'console']
    if config['output'] not in valid_outputs:
        raise ValueError(f"Invalid output '{config['output']}'. Must be one of: {valid_outputs}")
    
    return config

def load_csv(file_path):
    #check if csv file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV data file not found: {file_path}")
    
    #load csv data and transform it
    with open(file_path, 'r', encoding='utf-8') as f:
        #dictreader takes care of header row
        reader = csv.DictReader(f)
        #list of dictionaries, each representing a row
        raw_rows = list(reader)
        
    if not raw_rows:
        raise ValueError("CSV file is empty or contains no data rows.")
    
    #transform data to have one row per country-year
    transformed = []
    for row in raw_rows:
        #remove leading/trailing whitespace from keys and values
        country_name = row.get('Country Name', '').strip()
        country_code = row.get('Country Code', '').strip()
        continent = row.get('Continent', '').strip()
        
        #get all year columns 
        years = [k for k in row.keys() if k.isdigit()]
        
        #for each year, create a new row
        for yearcol in years:
            value = row.get(yearcol, '').strip()
            if value:
                transformed.append({
                    "Country Name": country_name,
                    "Country Code": country_code,
                    "Region": continent,  # Use Continent as Region
                    "Year": yearcol,
                    "Value": value,
                })
                
    return transformed

# Clean and validate data
def _parse_year(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

def _parse_gdp(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
    
def clean_data(raw_rows):
    # Strip whitespace from keys and values
    stripped_rows = list(map(lambda row: 
        {k.strip(): v.strip() if isinstance(v, str) 
         else v for k, v in row.items()}, raw_rows))
    # Parse Year and Value to correct types
    parsed_rows = list(
        map(lambda row: {
            "Country Name": row.get("Country Name", ""),
            "Country Code": row.get("Country Code", ""),
            "Region": row.get("Region", ""),
            "Year": _parse_year(row.get("Year", "")),
            "Value": _parse_gdp(row.get("Value", "")),
        }, stripped_rows)
    )
    # Filter out rows with missing or invalid data
    cleaned = list(
        filter(lambda row: 
               row["Country Name"] and 
               row["Country Code"] and 
               row["Region"] and 
               row["Year"] is not None and 
               row["Value"] is not None, 
               parsed_rows)
    )
    
    return cleaned


def load_and_clean_data(file_path):
    raw = load_csv(file_path)
    return clean_data(raw)

    
    

    
    
