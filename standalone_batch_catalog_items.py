VERSION = "0.2"
#This version of the script is meant to be run as a stand alon script and not via a notbook. 

from arcgis.gis import GIS
from arcgis.gis import Item
from arcgis.gis import ContentManager
from arcgis import __version__
from arcgis.mapping.ogc import CSVLayer
from datetime import datetime, date
import ipywidgets as widgets
import sys
import numpy as np
from itertools import islice

import pandas as pd
import tempfile

import os
import uuid
import json
import shutil
import tempfile
import time

from getpass import getpass


import xlsxwriter
import networkx as nx

print('Start')

# Define global variables
MY_ORG = "home"  # Org to view content
ORG_USER = "retail_transfer"  # Username
ORG_PASSWORD = 'SE.transfer.2023'
ORG_URL = r"https://commteamretail.maps.arcgis.com/"
CSV_ITEM_ID = "7da942c387ce40c7942aee822ed7348c"
local_path = r'C:\temp\retail'

#______________________________________________________________
INFO_PRODUCTS = ["Hub Page", "Web Mapping Application", "Dashboard", "Report Template", "StoryMap", "Form"]

RELATIONSHIP_TYPES = frozenset(['Map2Service', 'WMA2Code',
                                'Map2FeatureCollection', 'MobileApp2Code', 'Service2Data',
                                'Service2Service'])

# Set Pandas display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

def flatten_data(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

# source: https://stackoverflow.com/questions/56802797/digraph-parallel-ordering

def topological_sort_grouped(G):
    """
    Performs a topological sort where nodes entering the queue at the same time are stored in the same element. 
    
    Arguments:
        - G: <Networkx Directed Graph>
    Returns:
        - <iterator>
        
    Source: https://stackoverflow.com/questions/56802797/digraph-parallel-ordering
    """
    indegree_map = {v: d for v, d in G.in_degree() if d > 0}
    zero_indegree = [v for v, d in G.in_degree() if d == 0]
    while zero_indegree:
        yield zero_indegree
        new_zero_indegree = []
        for v in zero_indegree:
            for _, child in G.edges(v):
                indegree_map[child] -= 1
                if not indegree_map[child]:
                    new_zero_indegree.append(child)
        zero_indegree = new_zero_indegree

def chunks(lst, n):
    """
    Divides a lst into chunks of size n.
    """
    
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def report_to_csv(usern,reportdf,out_path):
    today = date.today()
    today_str = today.strftime("%b-%d-%Y")

    report_name = f"{usern}_contentReport_{today}.xlsx"
    report_path = os.path.join(out_path, report_name)

    #writer = pd.ExcelWriter(report_name, engine="xlsxwriter")
    writer = pd.ExcelWriter(report_path, engine="xlsxwriter")
    reportdf.to_excel(writer, sheet_name="Report", startrow=1, header=False)

    workbook = writer.book
    worksheet = writer.sheets['Report']

    # custom header for report following esri style guideline
    header_format = workbook.add_format({'bold': True,
                                         'bottom': 2,
                                         'bg_color': "#C7EAFF"})
    # format for edge items
    edge_format = workbook.add_format({'bg_color': "#BDF2C4"})

    # write the custom header
    for col_num, value in enumerate(reportdf.columns.values):
        worksheet.write(0, col_num + 1, value, header_format)


    # change the row background color if item is a 'edge' item, meaning it has no related items or dependencies downstream
    for row in range(len(reportdf)):
        if reportdf.iloc[row]['Related Items'] == '':
            worksheet.set_row(row + 1, cell_format=edge_format)

    #worksheet.autofit()

    writer.save()

def user_content_report(uPD):
    # Create an empty DataFrame
    dataframes = {}
    data = {'Name': [], 'Folder Count': [], 'Item Count': [],'Start Time':[], 'End Time': [],'Processing Time': []}
    df = pd.DataFrame(data)
    for index, row in uPD.iterrows():
        nows = datetime.now()
        start = nows.strftime("%m/%d/%Y %H:%M:%S")
        me = gis.users.search(row['Username'])[0]
        print(me)
        print(me.idpUsername)
        my_items = me.items(max_items = 99999)

        folders = me.folders
        

        if len(folders) > 0:
            for folder in folders:
                folder_items = me.items(folder=folder['title'], max_items=9999)
                for item in folder_items:
                    if item.type in INFO_PRODUCTS:
                        my_items.append(item)

        ##Filter out known issues
        #my_items['tags']

        ##Run through items to populate the catalog
        dict_list = []

        if len(my_items) > 0:
            # Add a new row to the DataFrame
            new_row = {'Name': me.fullName, 'Folders': len(folders), 'Items': len(my_items),'Start Time':start}
            # Initialize the DataFrame if it's the first iteration
            if df.shape[0] == 0:
                df = pd.DataFrame([new_row])
            else:
                # Append rows to the DataFrame from the second iteration onwards
                df = df.append(new_row, ignore_index=True)
            print(df)
            last_index = df.index[-1]
            
            print('dictionary started')
            for chunk in chunks(my_items, 100):
                for item in my_items:

                    # format item sharing data
                    item_share = ""
                    if item.shared_with['everyone']:
                        item_share += "Shared with everyone"
                    if item.shared_with['org']:
                        item_share += "Shared with org"

                    # delete protection string
                    if item.protect:
                        deletion_status = "True"
                    else:
                        deletion_status = "False"

                    # check if its xferred
                    if item.id in catalog['source_id'].unique():
                        xfer = "True"
                    else:
                        xfer = "False"

                    # last edit string
                    last_edit = datetime.fromtimestamp(item.modified/1000).__str__()

                    # get related items (heavy resource cost)
                    related_ids = []
                    item_json = item.get_data(try_json=True)
                    flat_keys = flatten_data(item_json)

                    #for k, v in flat_keys.items():
                    #    if "itemId" in k:
                    #        related_ids.append(v)
                    for k, v in flat_keys.items():
                        if "itemId" in k:
                            if not any(i in v for i in '!@#$%^&*()_-=+/,.<>[]{;}:'):
                                related_ids.append(v)

                    for fldr in folders:
                        if fldr['id']==item.ownerFolder:
                            fldr_name =fldr['title']
                        else:
                            fldr_name = 'root'

                    related_ids = set(related_ids)
                    if len(related_ids) == 0:
                        related_ids = ""

                    # loop and generate these dictionaries, store in a list
                    d = {"Item Name": item.title, "Author": item.owner, "Sharing": item_share, "Description": item.description, "Item ID": item.id, "Groups": item.shared_with['groups'],
                                        "Date Updated": last_edit, "URL": item.homepage, "Type": item.type, "Folder": fldr_name, "Tags": item.tags, "Categories": item.categories, 
                                        "Content Status": item.content_status, "Related Items": related_ids, "Delete Protection": deletion_status, "Transfer Status": xfer}

                    dict_list.append(d)
                    del d
                print('Chunk run')
            print('dictionary done')
            #print(dict_list)
            nowe = datetime.now()
            end = nowe.strftime("%m/%d/%Y %H:%M:%S")
            sedelta = (nowe-nows)
            df.loc[last_index, 'End Time'] = end
            df.loc[last_index, 'Processing Time'] = sedelta
            print(df)
            print("Dataframe generated successfully for {}.".format(row['Username']))

            report = pd.DataFrame(dict_list)
            report.to_csv(os.path.join(local_path,'last_iteration.csv'), index=False)
            report['Project ID'] = np.empty((len(report), 0)).tolist()
            print(report)
            # Get the column headers (column names)
            column_headers = report.columns

            # Convert the column headers to a list if needed
            column_headers_list = column_headers.tolist()

            print(column_headers)
            print(column_headers_list)
            
            graph_view = report[['Item ID', 'Related Items']]
            graph_view = graph_view.loc[graph_view['Related Items'] != '']

            graph_data = {}

            for item in range(len(graph_view)):
                graph_data[graph_view.iloc[item]['Item ID']] = list(graph_view.iloc[item]['Related Items'])
        
            user_graph = nx.DiGraph(graph_data)

            #print("Visual representation of user's item dependencies: ")
            #nx.draw_networkx(user_graph)
            print(user_graph)

            if user_graph.number_of_nodes() > 0:

            
                roots = list(topological_sort_grouped(user_graph))[0]

                for root in roots:
                    x = str(uuid.uuid4())[:8]
                    # filter for root project
                    report.loc[report["Item ID"] == root, "Project ID"] = x
                    relates = report.loc[report['Item ID'] == root]["Related Items"].values[0]
                    for item in relates:
                        # condition where project ids have already been added 
                        report.loc[(report["Item ID"] == item) & (report["Project ID"].str.len() != 0), "Project ID"] = x + ", "
                        # condition where a project id does not already exists
                        report.loc[(report["Item ID"] == item) & (report["Project ID"].str.len() == 0), "Project ID"] = x

                
                #print(row['Username'][:8])

            # Store the DataFrame in the dictionary with the row['Username'][:8] string as the key
            dataframes[row['Username'][:8]] = report
            report_to_csv(row['Username'],dataframes[row['Username'][:8]],local_path)
            print("Excel report generated successfully for {}.".format(row['Username']))
    print(df)
    return dataframes
#______________________________________________________________

# Establish GIS connection
#origin_pass = getpass(prompt=f"Enter the password for user {ORIGIN_TRANSFER_USER}: ")
print("Connecting ...")
#gis =GIS("home", expiration=9999)
gis = GIS(url=ORG_URL, username=ORG_USER, password=ORG_PASSWORD)
print("Connection successful.")
print("Logged into portal as: " + gis.properties.user.username)


# Get the template csv for the catalog structure
#CSV_ITEM_ID = "87da97f9c4b144c8a01cf91949d9d2da"
csvItem = gis.content.get(CSV_ITEM_ID)
catalog = CSVLayer(csvItem).df

# Get a list of all users in the organization
users = gis.users.search(max_users=10000)

# Create an empty Pandas DataFrame to store user details
user_data = pd.DataFrame(columns=['Processed','Username', 'Full Name', 'Email', 'User Type', 'Role', 'Description', 'Provider', 'Tag'])

# Iterate through the users and populate the DataFrame
for user in users:
    user_data = user_data.append({
        'Processed': time.time(),
        'Username': user.username,
        'Full Name': user.fullName,
        'Email': user.email,
        'User Type': user.userType,
        'Role': user.role,
        'Description': user.description,
        'Provider': user.provider,
        'Tag': user.tags
    }, ignore_index=True)

user_data

# Filtering out users that have already been cataloged 
#tocat_df = user_data[user_data['Tag'].apply(lambda x: 'cataloged' not in x)]
#tocat_df = user_data[user_data['Username'].apply(lambda x: 'robe8665@esri.com_manucomm' in x)]
#tocat_df


r= user_content_report(user_data)
r
print("Script Complete")

