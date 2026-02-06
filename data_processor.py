
#functions to filter data based on specific criteria
def filter_by_region(data,region):
    return list(filter(lambda row:row["Region"]==region,data))


def filter_by_year(data,year):
    return list(filter(lambda row:row["Year"]==int(year),data))

def filter_by_country(data,country):
    return list(filter(lambda row:row["Country Name"]==country,data))

def compute_average(values):
    return sum(values)/len(values)if values else 0.0

def compute_sum(values):
    return sum(values)


#function to group data by a specified key
def _group_by_key(data,key):
    #Extract unique values for the specified key
    unique_keys= list(set(map(lambda row:row[key],data)))
    #Create a dictionary where each unique key maps to a list of corresponding "Value" entries
    return {
        k: [row["Value"] for row in data if row[key] == k]
        for k in unique_keys
    }

#region-wise statistics based on the specified operation (average or sum)
def region_wise_stats(data,operation):
    #Determine the appropriate function based on the operation
    op_func = compute_average if operation == "average" else compute_sum
    grouped = _group_by_key(data, "Region")
    #Apply the chosen function to each group and return the results as a dictionary
    return {region: op_func(vals) for region, vals in grouped.items()}

#country-wise average GDP calculation
def country_average_gdp(data,country):
    
    #Filter the data for the specified country and compute the average GDP
    country_data = filter_by_country(data, country)
    
    #Extract the "Value" entries and compute the average
    
    values = list(map(lambda row: row["Value"], country_data))
    return compute_average(values)

#region-wise total GDP calculation
def region_sum_gdp(data,region):
    
    #Filter the data for the specified region and compute the total GDP
    region_data = filter_by_region(data, region)
    
    #Extract the "Value" entries and compute the sum
    
    values = list(map(lambda row: row["Value"], region_data))
    return compute_sum(values)

#year-wise GDP aggregation based on the specified operation (average or sum)
def year_wise_gdp(data,operation):
    
    #Determine the appropriate function based on the operation
    op_func = compute_average if operation == "average" else compute_sum
    grouped = _group_by_key(data, "Year")
    
    #Apply the chosen function to each group and return the results as a dictionary
    
    return {year: op_func(vals) for year, vals in grouped.items()}

def country_year_gdp(data,country):
    
    #Filter the data for the specified country and create a dictionary mapping years to GDP values
    
    country_data = filter_by_country(data, country)
    return {row["Year"]: row["Value"] for row in country_data}.items()


# Main Data Processing Function
def process_data(data, config):
    # Extract configuration parameters
    operation = config["operation"]
    region = config["region"]
    year = config["year"]
    # Perform filtering and computations
    filtered_by_region = filter_by_region(data, region)
    filtered_by_year = filter_by_year(data, year)
    
    # Compute statistic for the specified region
    region_values = list(map(lambda row: row["Value"], filtered_by_region))
    op_func = compute_average if operation == "average" else compute_sum
    region_stat = op_func(region_values)
    
    region_stats = region_wise_stats(data, operation)
    
    year_stats = year_wise_gdp(data, operation)
    
    # Get country-wise GDP for the specified year in the region
    region_year_data = list(
        filter(lambda row: row["Region"] == region and row["Year"] == int(year), data)
    )
    # Create a dictionary mapping country names to their GDP values for the specified year in the region
    region_year_countries = {
        row["Country Name"]: row["Value"] for row in region_year_data
    }
    # Get top 5 countries in the region by GDP for the specified year
    top_countries_in_region = dict(sorted(
        region_year_countries.items(), key=lambda item: item[1], reverse=True
    )[:5])
    
    # Compute year-wise trend for the region
    region_trend = {}
    for yr in sorted(set(map(lambda r: r["Year"], data))):
        region_data_year = filter_by_year(filter_by_region(data, region), yr)
        if region_data_year:
            values = list(map(lambda r: r["Value"], region_data_year))
            region_trend[yr] = op_func(values)
            
    # Compile all results into a single dictionary to return
    return {
        "config_summary": {
            "region": region,
            "year": year,
            "operation": operation,
            "output": config["output"],
        },
        "filtered_region_count": len(filtered_by_region),
        "filtered_year_count": len(filtered_by_year),
        "region_stat": region_stat,
        "region_stats_by_year": region_stats,
        "year_stats_global": year_stats,
        "region_year_countries": region_year_countries,
        "top_countries_in_region": top_countries_in_region,
        "region_trend": region_trend,
    }
    
