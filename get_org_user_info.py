import pandas as pd
from arcgis.gis import GIS
from datetime import datetime
import os

# Define global variables
MY_ORG = "home"  # Org to view content
ORG_USER = "realestate_transfer"  # Username
ORG_PASSWORD = 'SE.transfer.2023'
ORG_URL = r"https://arcgis.com//"
local_path = r'C:\Users\john7126\OneDrive - Esri\Documents - Commercial - Solution Engineer Team\Solution Engineering Resources\Industry Org Migration\CGS Content\Content Reports'

oldest_date = datetime(1, 1, 1)
# Establish GIS connection
#origin_pass = getpass(prompt=f"Enter the password for user {ORIGIN_TRANSFER_USER}: ")
print("Connecting ...")
#gis =GIS("home", expiration=9999)
gis = GIS(url=ORG_URL, username=ORG_USER, password=ORG_PASSWORD)
print("Connection successful.")
print("Logged into portal as: " + gis.properties.user.username)

# Get the organization information
org_info = gis.properties
org_short_name = org_info['urlKey'] if 'urlKey' in org_info else ''
print(org_short_name)

# Get all users in the organization
all_users = gis.users.search()

# Create a DataFrame to store user information
user_data = []

# Iterate through each user and gather relevant information
for user in all_users:
    user_items = gis.content.search(query=f'owner:{user.username}')
    total_items = len(user_items)
    user_info = {
        "Username": user.username,
        "Name": user.fullName,
        #"First Name": user.firstName,
        #"Last Name": user.lastName,
        "Username": user.username,
        "Email": user.email,
        "User Level": user.level,
        "Role": user.role,
        "Last Login": user.lastLogin,
        "User ID": user.id,
        "Number of Items":total_items, 
        "Report Complete": "No",
        "Last Reported":oldest_date.strftime("%m/%d/%Y %H:%M:%S")
    }
    user_data.append(user_info)

# Create a DataFrame from the list of user information
df = pd.DataFrame(user_data)

# Create a DataFrame from the list of user information
df = pd.DataFrame(user_data)

# Save the DataFrame to a CSV file
csv_filename = "{0}_all_users.csv".format(org_short_name)
df.to_csv(os.path.join(local_path,csv_filename), index=False)

print(f"CSV file '{csv_filename}' created with information of all users.")
