
############ RUN ROADS.PY FIRST ##############

# Import libraries
import matplotlib.pyplot as plt
import pandas as pd
import pandas as pd

################### BRIDGES ON WRONG LOCATION #######################
#Read road and bridge file
road = pd.read_csv('data/_roads.tsv', sep='\t')
bridge = pd.read_csv("data/BMMS_overview.csv", delimiter=";") #Reads a file where commas are replaced by dots to match the coordinates in the roads file
#Merge road and bridge dataframe
merged_df = bridge.merge(road, on=['road'], how='left')

def find_corresponding_lrp(row, df):
    lrp = row['LRPName']
    lrp_2 = row['LRPName'][:6]
    found_index = None
    
    # look for matching LRP for bridge and road
    for i, col in enumerate(df.columns[19:-2], start=19):  
        if row[col] == lrp:
            found_index = i  # Store the index of the matching column
            break
        
    # If no match is found look for similair same 6 digits in LRP name (so lrp001a and lrp001 is a match)
    if found_index is None:
        for i, col in enumerate(df.columns[19:-2], start=19):  
            if row[col] == lrp_2:
                found_index = i  # Store the index of the matching column
                break
    
    # If a match is found, get the next two column values for the lon and lat
    if found_index is not None and found_index + 1 < len(df.columns):
        row['lrp'] = row.iloc[found_index]
        row['lrp_lat'] = row[df.columns[found_index + 1]] if found_index + 1 < len(df.columns) else None
        row['lrp_long'] = row[df.columns[found_index + 2]] if found_index + 2 < len(df.columns) else None
    else:
        row['lrp']= None
        row['lrp_lat'] = None
        row['lrp_long'] = None

    return row

# Apply function for every row and create new dataframe
df = merged_df.apply(find_corresponding_lrp, axis=1, df=merged_df)

# Copy the dataframe with only relevant columns
selected_columns = ["road", "LRPName","name","lat","lon","lrp", "lrp_lat", "lrp_long"]
df_copy = df[selected_columns].copy()
#Make lat and lon columns a string
lat_long = ["lat", "lon", "lrp_lat", "lrp_long"]
df_copy[lat_long] = df_copy[lat_long].astype(str)

# Remove the decimal point and take the first 5 numbers from each column, so lat/lon and lrp lat/lon match with amount of decimals
df_copy[lat_long] = df_copy[lat_long].apply(lambda x: x.str.replace('.', '', regex=False))
df_copy[lat_long] = df_copy[lat_long].astype(str).apply(lambda x: x.str[:5])
df_copy[lat_long] = df_copy[lat_long].astype(float)
df_copy[lat_long] = df_copy[lat_long]/1000

def check_coordinates(df):
    # Scale everything so all coordinates have the same amount of decimals
    def scale_column(column):
        return (column * 1000).where(column <= 0.1, 
               (column * 100).where(column <= 1, 
               (column * 10).where(column <= 10, column)))

    # Apply scaling
    df['lat'] = scale_column(df['lat'])
    df['lon'] = scale_column(df['lon'])
    df['lrp_lat'] = scale_column(df['lrp_lat'])
    df['lrp_long'] = scale_column(df['lrp_long'])

    # Find all lat or lon who differ greatly from the corresponding lrp
    mask = (abs(df['lat'] - df['lrp_lat']) >= 0.2) | (abs(df['lon'] - df['lrp_long']) >= 0.2)
    
    # replace for those bridges the coordinates with the coordinates of the lrp
    df.loc[mask, 'lat'] = df.loc[mask, 'lrp_lat']
    df.loc[mask, 'lon'] = df.loc[mask, 'lrp_long']


check_coordinates(df_copy)

#Replace the coordinates in the original dataset
bridge["lat"]=df_copy["lat"]
bridge["lon"]=df_copy["lon"]



############### REMOVING DUPLICATE BRIDGES #################### 

# copy previously used dataframe
df = bridge.copy() 

# Make new column based in LRPName, first 3 letters of name and sub-division. Helps checking for the duplicates
df['dup_code'] = df['LRPName'].astype('str') + df['name'].str.extract(r'(\w{5})')[0].str.upper().fillna('x') + df['sub-division'].astype('str')

# Define the preference order as a dictionary, the data originating from certain datasets is preferred over others
preference_order = {
    'road_chainage': 6,
    'road_precise': 5,
    'bcs1': 4,
    'road_interpolate': 3,
    'bcs1_zerosec': 2,
    'error': 1
}

# Create a new column to assign scores based on the EstimatedLoc preference
df['EstimatedLoc_score'] = df['EstimatedLoc'].map(preference_order)
df.head()

# Sort the dataframe by 'dup_code' and 'loc_score' so the highest preference comes first
df_sorted = df.sort_values(by=['dup_code', 'EstimatedLoc_score'], ascending=[True, False])

# Drop duplicates based on 'dup_code', keeping the first occurrence (which has the highest loc_score)
df_cleaned = df_sorted.drop_duplicates(subset='dup_code', keep='first')

# Drop the temporary 'loc_score' column as it's no longer needed
df_notsorted = df_cleaned.drop(['EstimatedLoc_score', 'dup_code'], axis=1)

# Sort the DataFrame by its index in ascending order
df_final = df_notsorted.sort_index()

# Overwrite the excisting excel file
with pd.ExcelWriter("infrastructure/BMMS_overview.xlsx", mode="a", if_sheet_exists="replace") as writer:
    df_final.to_excel(writer, sheet_name="BMMS_overview", index=False)
