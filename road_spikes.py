# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from setuptools.command.install import install

roads = pd.read_csv("_roads.tsv", sep="\t", low_memory=False)

# %%
roads

# %%
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

# Create the plot
plt.figure(figsize=(8, 6))

# Plot the road (first row)
plt.plot(longitudes, latitudes, marker='o', markersize=5, linestyle='-', color='blue', alpha=0.7, label=f'{road_name}')

# Customize the plot
plt.title(f'Road: {road_name}')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)
plt.legend()

# Show the plot
plt.show()

# %%
import pandas as pd
import math

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
df = pd.read_csv('_roads.tsv', sep='\t', header=0, low_memory=False)

# Apply the outlier fixing function to each row.
df_fixed = df.apply(fix_road_row, axis=1)

# Save the adjusted DataFrame to a new TSV file.
#df_fixed.to_csv('fixed_roads.tsv', sep='\t', index=False)
print("Finished processing. Check 'fixed_roads.tsv' for the adjusted data.")


# %%
import matplotlib.pyplot as plt
import pandas as pd

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
    
    plt.title(f'Coordinate Comparison for Road: {road_name}')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.legend()
    plt.show()

# Example usage:
# Assuming you have already loaded your DataFrames as 'roads' and 'df_fixed',
# to compare the first row (index 0), run:
plot_road_comparison_by_index(24, roads, df_fixed)


# %%



