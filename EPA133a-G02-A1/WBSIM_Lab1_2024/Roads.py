import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from math import *

roads = pd.read_csv('data/_roads.tsv', sep="\t", low_memory=False)


roads


row = roads.iloc[0]

# Extract the name of the road (first column)
road_name = row.iloc[0]

# Extract latitude and longitude values from the row
latitudes = []
longitudes = []

# Extract latitude and longitude for each LRP
for i in range(1, len(row), 3):  # every 3rd column is latitude and longitude
    latitudes.append(row.iloc[i+1])   # Column i+1 is latitude
    longitudes.append(row.iloc[i+2])  # Column i+2 is longitude





def haversine(lat1, lon1, lat2, lon2):
    """
    Compute the great-circle distance between two points on Earth in kilometers.
    """
    # Convert decimal degrees to radians.
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) 
    r = 6371  # Radius of Earth in kilometers.
    return r * c

def fix_road_row(row, threshold=1.2):
    """
    Process a single road (row) with the following assumptions:
      - Column 0: road identifier.
      - The remaining columns are in repeating groups of three: [LRP name, latitude, longitude].
      - Once latitude or longitude is NaN, no more valid points follow.
      
    For each internal point, the function computes the "direct" haversine distance between its neighboring
    points and compares it with the "route" distance (previous->current plus current->next). If the route 
    distance exceeds threshold * direct distance, the current point is replaced by the average of its neighbors.
    """
    # Total number of columns after the first (road) column.
    total_cols = len(row) - 1
    num_groups = total_cols // 3  # Number of LRP groups.
    
    valid_groups = []  # List of group indices that have valid (non-NaN) lat/lon.
    lats = []
    lons = []
    
    # Extract groups in order until a NaN is encountered.
    for i in range(num_groups):
        # Group i: LRP at index 1+3*i, lat at index 2+3*i, lon at index 3+3*i.
        lat_val = pd.to_numeric(row.iloc[1 + 3*i + 1], errors='coerce')
        lon_val = pd.to_numeric(row.iloc[1 + 3*i + 2], errors='coerce')
        if pd.isna(lat_val) or pd.isna(lon_val):
            break
        valid_groups.append(i)
        lats.append(lat_val)
        lons.append(lon_val)
    
    # Need at least three valid points to check an internal point.
    if len(valid_groups) < 3:
        return row

    # Create Series for latitudes and longitudes with the group indices.
    lat_series = pd.Series(lats, index=valid_groups)
    lon_series = pd.Series(lons, index=valid_groups)
    
    # Create shifted series to obtain previous and next values.
    prev_lat = lat_series.shift(1)
    next_lat = lat_series.shift(-1)
    prev_lon = lon_series.shift(1)
    next_lon = lon_series.shift(-1)
    
    # Iterate over internal valid points (skip first and last).
    for i in valid_groups[1:-1]:
        curr_lat = lat_series.loc[i]
        curr_lon = lon_series.loc[i]
        
        # Compute the direct distance between the previous and next points.
        d_direct = haversine(prev_lat.loc[i], prev_lon.loc[i], next_lat.loc[i], next_lon.loc[i])
        # Compute the route distance: previous->current + current->next.
        d_route = haversine(prev_lat.loc[i], prev_lon.loc[i], curr_lat, curr_lon) + \
                  haversine(curr_lat, curr_lon, next_lat.loc[i], next_lon.loc[i])
        
        # If the route distance significantly exceeds the direct distance, consider it an outlier.
        if d_route > threshold * d_direct:
            # Replace with the average of the neighboring points.
            new_lat = (prev_lat.loc[i] + next_lat.loc[i]) / 2
            new_lon = (prev_lon.loc[i] + next_lon.loc[i]) / 2
            lat_series.loc[i] = new_lat
            lon_series.loc[i] = new_lon
    
    # Write the corrected lat/lon values back into the row.
    for i in valid_groups:
        # lat: column index = 1 + 3*i + 1, lon: column index = 1 + 3*i + 2.
        row.iloc[1 + 3*i + 1] = lat_series.loc[i]
        row.iloc[1 + 3*i + 2] = lon_series.loc[i]
        
    return row

# Read the TSV file.
# low_memory=False is used to avoid dtype warnings.
df = pd.read_csv('infrastructure/_roads.tsv', sep='\t', header=0, low_memory=False)

# Apply the outlier fixing function to each row.
df_fixed = df.apply(fix_road_row, axis=1)

# Save the adjusted DataFrame to a new TSV file.
df_fixed.to_csv('infrastructure/_roads.tsv', sep='\t', index=False)
df_fixed.to_csv('data/_roads.tsv', sep='\t', index=False)
print("Finished processing. Check 'fixed_roads.tsv' for the adjusted data.")


def extract_coordinates_from_row(row, lrp_start_index=1):
    """
    Given a row from a DataFrame (with columns arranged in groups of three: [LRP name, latitude, longitude] 
    starting after the first column which is the road name), this function extracts the valid latitude 
    and longitude values.
    """
    latitudes = []
    longitudes = []
    # Iterate over the row in groups of three starting at index 'lrp_start_index'
    for i in range(lrp_start_index, len(row) - 2, 3):
        try:
            # Use iloc indexing: 
            # Group structure: [LRP name, latitude, longitude] so latitude is at i+1 and longitude at i+2.
            lat = pd.to_numeric(row.iloc[i + 1], errors='coerce')
            lon = pd.to_numeric(row.iloc[i + 2], errors='coerce')
            if pd.notna(lat) and pd.notna(lon):
                latitudes.append(lat)
                longitudes.append(lon)
        except IndexError:
            print(f"Skipping index {i+1} or {i+2}, out of bounds.")
    return latitudes, longitudes

def plot_road_comparison_by_index(row_index, roads, df_fixed, lrp_start_index=1):
    """
    Extracts the row corresponding to row_index from both the original 'roads' DataFrame 
    and the cleaned 'df_fixed' DataFrame using iloc[], and plots their coordinates for comparison.
    
    The first column (index 0) is assumed to be the road name.
    """
    # Extract the rows using iloc
    row_old = roads.iloc[row_index]
    row_new = df_fixed.iloc[row_index]
    
    # Extract the road name (assumed to be in the first column)
    road_name = row_old.iloc[0]
    
    # Get the coordinate lists for both datasets
    lat_old, lon_old = extract_coordinates_from_row(row_old, lrp_start_index)
    lat_new, lon_new = extract_coordinates_from_row(row_new, lrp_start_index)
    
    plt.figure(figsize=(10, 8))
    if lat_old and lon_old:
        plt.plot(lon_old, lat_old, marker='o', markersize=5, linestyle='-', color='blue',
                 alpha=0.7, label=f'Original: {road_name}')
    else:
        print("No valid coordinates found for the original data.")
        
    if lat_new and lon_new:
        plt.plot(lon_new, lat_new, marker='o', markersize=5, linestyle='--', color='red',
                 alpha=0.7, label=f'Cleaned: {road_name}')
    else:
        print("No valid coordinates found for the cleaned data.")
    
   


############################ CONNECTING ROADS ######################################################################

filepath2 = "infrastructure/_roads.tsv"  # Correct relative path
roads_df = pd.read_csv(filepath2, sep='\t', low_memory=False)

# Change column names 

# Get the existing column names as a list
cols = list(roads_df.columns)

# The first 7 columns remain unchanged: 
# 'road', 'lrp1', 'lat1', 'lon1', 'lrp2', 'lat2', 'lon2'
new_cols = cols[:7]

# For each subsequent column, determine its group and type
for i in range(len(cols) - 7):
    group = 3 + i // 3  # group number starts at 3
    mod = i % 3        # determines which of lrp/lat/lon it is
    if mod == 0:
        new_cols.append(f"lrp{group}")
    elif mod == 1:
        new_cols.append(f"lat{group}")
    elif mod == 2:
        new_cols.append(f"lon{group}")

# Update the dataframe columns
roads_df.columns = new_cols

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

# Function to find last non-NaN lat/lon per road
def get_last_valid_lat_lon(row):
    """Returns the last valid latitude and longitude in the row"""
    lat_cols = [col for col in roads_df.columns if col.startswith("lat")]
    lon_cols = [col for col in roads_df.columns if col.startswith("lon")]

    last_valid_lat = row[lat_cols].dropna().iloc[-1] if row[lat_cols].dropna().any() else None
    last_valid_lon = row[lon_cols].dropna().iloc[-1] if row[lon_cols].dropna().any() else None

    return last_valid_lat, last_valid_lon

# Create summary DataFrame
summary_data = []
for _, row in roads_df.iterrows():
    last_lat, last_lon = get_last_valid_lat_lon(row)
    summary_data.append([row["road"], row["lat1"], row["lon1"], last_lat, last_lon])

summary_df = pd.DataFrame(summary_data, columns=['road', 'begin_lat', 'begin_lon', 'end_lat', 'end_lon'])
# print(summary_df.isna().sum(axis=0))

# Show rows where any column has NaN values
nan_rows = summary_df[summary_df.isna().any(axis=1)]
# print(nan_rows)

summary_df_cleaned = summary_df.dropna()
# print(summary_df_cleaned.isna().sum(axis=0))

# Cleaned 

# Get unique road names
unique_roads = summary_df_cleaned['road'].unique()

# Print the unique road values
# print(unique_roads)

# Split roads into categories
summary_df_cleaned = summary_df_cleaned.copy()  # Ensure it's a full copy before modifying
summary_df_cleaned.loc[:, 'road_type'] = summary_df_cleaned['road'].str[0]
N_roads = summary_df_cleaned[summary_df_cleaned['road_type'] == 'N'].reset_index(drop=True)
R_roads = summary_df_cleaned[summary_df_cleaned['road_type'] == 'R'].reset_index(drop=True)
Z_roads = summary_df_cleaned[summary_df_cleaned['road_type'] == 'Z'].reset_index(drop=True)

def connect_roads(roads):
    """
    Orders roads by connecting each one to the nearest available road's end or start point.
    """
    if roads.empty:
        return roads

    ordered_roads = [roads.iloc[0]]  # Start with the first road
    roads = roads.iloc[1:].reset_index(drop=True)  # Remove from unprocessed list

    while not roads.empty:
        last_road = ordered_roads[-1]
        last_end_lat, last_end_lon = last_road['end_lat'], last_road['end_lon']

        # Compute distances
        distances = roads.apply(
            lambda row: haversine(last_end_lon, last_end_lat, row['begin_lon'], row['begin_lat']), axis=1
        )

        # Check if all values are NaN
        if distances.isna().all():
            print("Warning: No valid connection found. Stopping early.")
            break  # Stop if no valid roads remain

        closest_idx = distances.idxmin()
        ordered_roads.append(roads.loc[closest_idx])
        roads = roads.drop(closest_idx).reset_index(drop=True)

    return pd.DataFrame(ordered_roads)

# Connect roads per category
N_continuous = connect_roads(N_roads)
R_continuous = connect_roads(R_roads)
Z_continuous = connect_roads(Z_roads)

# Function to concatenate road data in the sequence specified by N_continuous
def concatenate_roads(roads_df, ordered_roads_df):
    """
    Concatenates road information in the order specified by ordered_roads_df.
    Creates a continuous road per category (N, R, Z) in a single row.
    """
    # Filter roads_df to keep only roads that exist in ordered_roads_df, maintaining order
    ordered_roads = ordered_roads_df['road'].tolist()
    filtered_roads = roads_df[roads_df['road'].isin(ordered_roads)].set_index('road').loc[ordered_roads].reset_index()

    # Extract LRP, Lat, Lon columns dynamically
    lrp_cols = [col for col in roads_df.columns if col.startswith('lrp')]
    lat_cols = [col for col in roads_df.columns if col.startswith('lat')]
    lon_cols = [col for col in roads_df.columns if col.startswith('lon')]

    # Initialize lists to store concatenated values
    lrp_list, lat_list, lon_list = [], [], []

    for _, row in filtered_roads.iterrows():
        # Extract non-null values for LRP, lat, and lon
        valid_lrps = row[lrp_cols].dropna().tolist()
        valid_lats = row[lat_cols].dropna().tolist()
        valid_lons = row[lon_cols].dropna().tolist()
        
        # Ensure lengths match before extending lists
        min_len = min(len(valid_lrps), len(valid_lats), len(valid_lons))
        lrp_list.extend(valid_lrps[:min_len])
        lat_list.extend(valid_lats[:min_len])
        lon_list.extend(valid_lons[:min_len])

    return lrp_list, lat_list, lon_list

# Concatenate roads for each category (N, R, Z)
n_lrps, n_lats, n_lons = concatenate_roads(roads_df, N_continuous)
r_lrps, r_lats, r_lons = concatenate_roads(roads_df, R_continuous)
z_lrps, z_lats, z_lons = concatenate_roads(roads_df, Z_continuous)

# Function to create a continuous road DataFrame in the desired format
def create_continuous_road_df(road_name, lrps, lats, lons):
    """
    Constructs a DataFrame with columns: road, lrp1, lat1, lon1, lrp2, lat2, lon2, ..., lrpn, latn, lonn.
    If lengths are different, missing values are filled with NaN.
    """
    max_length = max(len(lrps), len(lats), len(lons))  # Find the longest list
    
    # Ensure all lists are the same length by filling with NaN
    lrps.extend([None] * (max_length - len(lrps)))
    lats.extend([None] * (max_length - len(lats)))
    lons.extend([None] * (max_length - len(lons)))
    
    # Create column names dynamically
    columns = ['road'] + [f'lrp{i+1}' for i in range(max_length)] + \
              [f'lat{i+1}' for i in range(max_length)] + \
              [f'lon{i+1}' for i in range(max_length)]
    
    # Construct DataFrame row
    road_data = [road_name] + lrps + lats + lons
    road_df = pd.DataFrame([road_data], columns=columns)
    
    return road_df

# Create DataFrames for each continuous road category
n_roads_df = create_continuous_road_df('N_continuous', n_lrps, n_lats, n_lons)
r_roads_df = create_continuous_road_df('R_continuous', r_lrps, r_lats, r_lons)
z_roads_df = create_continuous_road_df('Z_continuous', z_lrps, z_lats, z_lons)

# Concatenate into final continuous roads DataFrame
continuous_roads_df = pd.concat([n_roads_df, r_roads_df, z_roads_df], ignore_index=True)

# Function to restructure the DataFrame to the _roads.tsv format with Unnamed columns
def restructure_continuous_roads_with_unnamed(continuous_roads_df):
    """
    Restructures the DataFrame into the format: 
    road, lrp1, lat1, lon1, lrp2, lat2, lon2, Unnamed: 7, Unnamed: 8, ..., Unnamed: N.
    """
    structured_data = []
    
    for _, row in continuous_roads_df.iterrows():
        road_name = row['road']
        
        # Extract LRPs, latitudes, and longitudes while preserving order
        lrps = row[[col for col in continuous_roads_df.columns if col.startswith('lrp')]].values.tolist()
        lats = row[[col for col in continuous_roads_df.columns if col.startswith('lat')]].values.tolist()
        lons = row[[col for col in continuous_roads_df.columns if col.startswith('lon')]].values.tolist()

        # Flatten the data into the required column sequence
        structured_row = [road_name]
        for i in range(len(lrps)):
            structured_row.extend([lrps[i], lats[i], lons[i]])

        structured_data.append(structured_row)
    
    # Create column names to the format of the same format as the _roads.tsv file
    max_length = max(len(row) for row in structured_data)
    base_columns = ['road', 'lrp1', 'lat1', 'lon1', 'lrp2', 'lat2', 'lon2']
    
    unnamed_columns = [f'Unnamed: {i+7}' for i in range(max_length - len(base_columns))]
    final_columns = base_columns + unnamed_columns

    # Convert structured data into a DataFrame
    structured_df = pd.DataFrame(structured_data, columns=final_columns)

    return structured_df

# Convert continuous_roads_df to the requested format
structured_continuous_roads_df = restructure_continuous_roads_with_unnamed(continuous_roads_df)

# Save the structured DataFrame to a TSV file
file_path = "infrastructure/_roads.tsv"
structured_continuous_roads_df.to_csv(file_path, sep='\t', index=False)
