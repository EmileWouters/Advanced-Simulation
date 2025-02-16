# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from setuptools.command.install import install

# %%
import os
os.chdir("/Users/florisvanamersfoort/Desktop/EPA/Q3/Advanced_Simulation/WBSIM_Lab1_2024")
print("✅ Changed working directory to:", os.getcwd())

# Now load the file
import pandas as pd
roads = pd.read_csv("_roads_copy.tsv", sep="\t", low_memory=False)
print("✅ File loaded successfully!")

# %%
# Let's take a look at the data
roads

# %% [markdown]
# # Looking at the Distances between LRP points
# 
# This first part of the code takes the _"_roads_copy.tsv"_ file and tries to work around the road spikes in the data as much as possible.

# %%
# First we need to take a look at the data, by creating a plot
plt.figure(figsize=(10, 8))

# Loop through each row in the dataframe 
for index, row in roads.iterrows():
    # Extract the name of the road, which can be found in the first column
    road_name = row.iloc[0]
    
    # Extract latitude and longitude values from the row
    latitudes = []
    longitudes = []
    
    # Extract latitude and longitude for each LRP, every 3rd column is latitude and longitude
    for i in range(1, len(row), 3):  
        latitudes.append(row.iloc[i+1])   # Column i+1 is latitude
        longitudes.append(row.iloc[i+2])  # Column i+2 is longitude
    
    # Plot the road (connecting the points)
    plt.plot(longitudes, latitudes, marker='o', label=f'{road_name}')


plt.title('All Roads')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)

plt.show()

# %%
# Now lets do the same again but, zooming into one road to take a closer look at the outliers shown in the "All roads" 
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

# %% [markdown]
# ## A closer look at the Distance between the LRP points for different roads, using a distance function
# The graph above showcases road N1, we can see it has a lot of outliers already. Now we take a more specific look at the quantification of these outliers

# %%
def find_distance(row):
    latitudes = []
    longitudes = []
    distances = np.array([])
    
    # The iteration jumps in 3 columns every run, starting column 1)
    for i in range(1, len(row),3):
        latitudes.append(row.iloc[i+1])
        longitudes.append(row.iloc[i+2])
        
    # Creating an iteration to calculate the distance between two LRP using Pythagoras theorem
    # The iterator starts at 1 to be able to access the previous point using j-1
    for j in range (1, len(latitudes)):
        distance= float(np.sqrt((latitudes[j]-latitudes[j-1])**2 + (longitudes[j]-longitudes[j-1])**2)) 
        distances= np.append(distances, distance)
    return distances

# %%
# We can see here the distances don't from a normal distibution
# You can change the index in line 4 to test other roads
import seaborn as sns
distances_row = find_distance(roads.iloc[330])
# Create a figure and axis
plt.figure(figsize=(12, 6))

# Plotting histogram to see the distribution
plt.subplot(1, 2, 1)  # (rows, columns, position)
plt.hist(distances_row, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
plt.title("Histogram of Distances")
plt.xlabel("Distance")
plt.ylabel("Frequency")

# Plotting box plot to identify outliers
plt.subplot(1, 2, 2)
sns.boxplot(data=distances_row, color='skyblue')
plt.title("Boxplot of Distances")
plt.ylabel("Distance")

# Show the plots
plt.tight_layout()
plt.show()


# %% [markdown]
# When we play around with the index in line 4 we see a lot of outliers for each single road.

# %% [markdown]
# ## Identifying Outliers and using a function to remove them
# To identify outliers, we use percentiles to recognize the LRPs whose distances deviate too much from the majority of distances. This method is preferred over standard deviation as the distribution is not normal in the roads. The correlation between the arrays is as follows:
# -  The index in the latitudes and longitudes arrays correspond to index + 1, and index +2 n the row of roads [], respectively.
# -  The index in the distances array corresponds to the distance between index and index +1 in the latitudes and longitudes arrays.
# -  If an LRP is an outlier, two consecutive distances in the distances array will be outliers. Thus, two consecutive indexes will be stored in outliers_index array. This way we can check for outliers every two indexes in the outliers_index array. 
# -  The content of the outlier_index array corresponds to the indexes of outliers in the distances array. This means that every second checked variable in the outlier_index array corresponds to the variable+1 location in the latitudes and longitudes arrays. 
# -  In the end, index+1 (so outliers_array-variable +1) in the latitudes array corresponds to the LRP at roads.iloc[index] in the roads dataframe. This means that the variable found in the outlier_index array corresponds to the index in the roads dataframe for the LRPs that are outliers. 
# 
# For example, say we take the data from the first 4 LRPs of the N1 road. The latitude and longitudes array will look like this (LRP 0,1,2,3): 
# - [a,b,c,d]
# - [e,f,g,h]
# 
# The distances array will look like this:
# $\left[\sqrt{(b-a)^2 + (f-e)^2}, \sqrt{(c-b)^2 + (g-f)^2}, \sqrt{(d-c)^2 + (h-g)^2}\right]$
# 
# If LRP2 (c,g) is an outlier, distances at positions 1 and 2 will be outliers, and the outliers_index array will look like this: [1,2].
# 
# Since we check the outliers_index array in a step of two, we will see the selected index wil be 1. The 1 from this array, corresponds to position 1+1 in the latitudes and longitudes arrays. This means that the outlier is LRP2 (c,g) and its index in the roads dataframe is 1.
# 
# 
#  

# %%
# Merging functions or using find_distances in here is possible, so that all the values are in one place. 
def find_outlier(distances):   #add longituted and latitude arrays as input
    # Finding the outliers
    outliers_index = []
    outliers_latitude = []
    outliers_longitude = [] 
    limit = np.percentile(distances,20)  # Adjust the percentile value as needed
    
    for i in range(len(distances)):
        if distances[i] > limit:
            outliers_index.append(i)

    #Store longitutes and latitudes that need to be eliminated form dataset to clear discontinuities
    #the below formula is not working, because the array where the longitutdes and longitudes are stores is not accesible in the function, so we need to modify the first function to return those arrays as well, or combine functions.
    for outlier_LRP in (outliers_index):
        print(f'Outlier found at index {outlier_LRP+1} in the .')
        #modify to look into the longitutde and latitude arrays
        outliers_latitude.append(roads.iloc[outlier_LRP*3+1]) # Multiply by 3 to take into account the 3 columns per LRP
        outliers_longitude.append(roads.iloc[outlier_LRP*3+2]) 
    
    return (outliers_index)
            #outliers_latitude, outliers_longitude) eliminated for debugging

# %%
#Testing the function on an individual road
distances_per_row= find_distance(roads.iloc[0])
find_outlier(distances_per_row)

# %%
# So we run into an out of bounds error, this could be due to some NaN values.
# Here we can check how many NaN values there are.
# Show only columns with NaN values
print("Columns with NaN values:\n", roads.isnull().sum()[roads.isnull().sum() > 0])

# Check how many rows have NaNs in key location columns
missing_lat_lon = roads[["lat1", "lon1", "lat2", "lon2"]].isnull().sum()
print("\nMissing values in important columns:\n", missing_lat_lon)

# %%
# So I have to decidde wether to intepolate or remove the NaN values...

# %%
#testing the find_outliers function on a made up dataset
test_data= np.array([ 7.87933335,  3.96690776,  1.20005889,  4.08106555,  9.0945608 ,
  6.24926475,  9.56687429,  2.04267342,  2.94189448,  5.54273577,
  8.66454794,  1.98329573,  2.03864279,  9.12630919,  1.09260143,
  9.5752253 ,  1.47606925,  9.35662125,  9.15188057,  9.05969162,
  7.29861896,  2.83379218,  2.81683824,  9.37257181,  9.19355721,
  8.39165449,  3.66811323,  8.41380903,  7.12615618,  9.27155382,
  3.20924606,  9.32447007,  7.91317994,  4.48005306,  2.8679023 ,
  4.72825505,  9.82844162,  8.71447804,  7.96209059,  3.96110497,
  7.29246835,  3.82898598,  6.20188668,  6.01289019,  4.28981876,
  6.85110954,  7.292056  ,  3.14969986,  9.81320412,  3.56321965,
  6.94331824,  1.24059123,  8.7137695 ,  6.12000909,  2.58015218,
  9.03457212,  9.40851736,  6.53592192,  2.88369518,  9.49166568,
  4.24520427,  2.0209155 ,  5.05715876,  8.94493934,  7.52394918,
  3.07112378,  5.05546684,  4.29700848,  5.00867744,  3.95829409,
  7.88646739,  5.63675517,  5.80670675,  5.31032564,  5.26111614,
  3.72993747,  2.12403482,  8.10681961,  5.97076286,  1.06158609,
  3.0695829 ,  7.62114897,  1.21930559,  1.75517103,  9.73531438,
  2.89574156,  8.34710458,  7.22402646,  5.2670128 ,  2.20312249,
  9.07012024,  7.62115936,  4.06148188,  1.27004129,  5.10740386,
  7.42073512,  6.87517948,  9.02588805,  9.06501345,  8.39061373,
  50.        , 55.        , 60.        ])

find_outlier(test_data)

# %%



