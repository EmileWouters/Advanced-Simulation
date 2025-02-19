# Code for removing duplicate bridges
# assumes either loading the Xlsx file. Adapt to work further on already loaded DF us necessary

# Import libraries
import matplotlib.pyplot as plt
import pandas as pd

# Path for loading the data
path = './WBSIM_Lab1_2024/infrastructure/'
file_name = 'BMMS_overview.xlsx'

raw_data = pd.read_excel(path + file_name, na_values='.') # Load the data from the Excel file


############### START OF RELEVANT ALGORTIHM #################### 


# IMPORTANT: If copied in other code, either load xlsx file again or use the already loaded data in the dataframe
df = raw_data.copy() 

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


########### ADD CODE HERE TO SAVE TO XLSXM FILE ####################