import numpy as np 
import pandas as pd 
from math import *
import matplotlib.pyplot as plt

# filepath = 'infrastructure\Roads_InfoAboutEachLRP.csv'
# lrp_df = pd.read_csv(filepath)

filepath2 = "infrastructure/_roads.tsv"

filepath2 = "infrastructure/_roads.tsv"  # Correct relative path
roads_df = pd.read_csv(filepath2, sep='\t', low_memory=False)

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
    
    # Ensure all lists are the same length by padding with NaN
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

# Function to restructure the DataFrame and name columns as per the requested format
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
    
    # Create column names dynamically: road, lrp1, lat1, lon1, lrp2, lat2, lon2, ..., Unnamed: 7, Unnamed: 8, ...
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
file_path = "infrastructure/_continuous_roads.tsv"
structured_continuous_roads_df.to_csv(file_path, sep='\t', index=False)

# # Extract latitude and longitude columns for Z roads
# lat_cols = [col for col in z_roads_df.columns if col.startswith("lat")]
# lon_cols = [col for col in z_roads_df.columns if col.startswith("lon")]

# # Flatten the latitude and longitude values
# z_lats = z_roads_df[lat_cols].values.flatten()
# z_lons = z_roads_df[lon_cols].values.flatten()

# # Remove NaN values
# valid_points = ~np.isnan(z_lats) & ~np.isnan(z_lons)
# z_lats = z_lats[valid_points]
# z_lons = z_lons[valid_points]

# # Plot the latitude vs longitude for Z roads
# plt.figure(figsize=(10, 6))
# plt.plot(z_lons, z_lats, marker='o', linestyle='-', color='b', label="Z Roads")

# plt.xlabel("Longitude")
# plt.ylabel("Latitude")
# plt.title("Z Roads: Latitude vs Longitude")
# plt.legend()
# plt.grid()
# plt.show()

# # Function to plot latitude vs longitude for a given road type
# def plot_road_lat_lon(road_df, road_name, color):
#     """
#     Plots latitude (y-axis) vs longitude (x-axis) for a given road DataFrame.
#     """
#     lat_cols = [col for col in road_df.columns if col.startswith("lat")]
#     lon_cols = [col for col in road_df.columns if col.startswith("lon")]

#     # Flatten the latitude and longitude values
#     lats = road_df[lat_cols].values.flatten()
#     lons = road_df[lon_cols].values.flatten()

#     # Remove NaN values
#     valid_points = ~np.isnan(lats) & ~np.isnan(lons)
#     lats = lats[valid_points]
#     lons = lons[valid_points]

#     # Plot
#     plt.figure(figsize=(10, 6))
#     plt.plot(lons, lats, marker='o', linestyle='-', color=color, label=road_name)
#     plt.xlabel("Longitude")
#     plt.ylabel("Latitude")
#     plt.title(f"{road_name}: Latitude vs Longitude")
#     plt.legend()
#     plt.grid()
#     plt.show()

# # Plot for N roads
# plot_road_lat_lon(n_roads_df, "N Roads", "r")

# # Plot for R roads
# plot_road_lat_lon(r_roads_df, "R Roads", "g")



