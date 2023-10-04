from arcgis.gis import GIS
from arcgis.gis import Item
from arcgis import __version__
from arcgis.mapping.ogc import CSVLayer
from datetime import datetime, date
import sys
import numpy as np
import timeit

import pandas as pd
import uuid

import networkx as nx

from utils import utils

def main():
    
    """CONSTANTS"""
    GIS_URL = str(sys.argv[1])
    CLIENT_ID = str(sys.argv[2])
    CSV_ITEM_ID = str(sys.argv[3])
    GIS_USER = str(sys.argv[4])
    
    # Establish GIS connection        
    print("Connecting ...")
    gis = GIS(GIS_URL, client_id=CLIENT_ID)
    print(f"Connection successful with identity {gis.properties.user.username}. This user will access the content of {GIS_USER}.")
    
        
    RELATIONSHIP_TYPES = frozenset(['Map2Service', 'WMA2Code',
                                    'Map2FeatureCollection', 'MobileApp2Code', 'Service2Data',
                                    'Service2Service'])

    INFO_PRODUCTS = ["Hub Page", "Web Mapping Application", "Dashboard", "Report Template", "StoryMap", "Form"]

    valid_items = []

    me = gis.users.search(GIS_USER)[0]
    my_items = me.items(max_items = 9999)

    for item in my_items:
        if item.type in INFO_PRODUCTS:
            valid_items.append(item)
        
    folders = me.folders

    for folder in folders:
        folder_items = me.items(folder=folder['title'], max_items=9999)
        for item in folder_items:
            if item.type in INFO_PRODUCTS:
                valid_items.append(item)
                                
    csvItem = gis.content.get(CSV_ITEM_ID)
    catalog = CSVLayer(csvItem).df
    
    dict_list = []

    def build_report(my_items=valid_items, dict_list=dict_list):
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
            flat_keys = utils.flatten_data(item_json)

            for k, v in flat_keys.items():
                if "itemId" in k:
                    related_ids.append(v)
            
            if len(folders) > 0:        
                for fldr in folders:
                    if fldr['id']==item.ownerFolder:
                        fldr_name =fldr['title']
                    else:
                        fldr_name = 'root'
            else:
                fldr_name = 'root'
                            
            related_ids = set(related_ids)
            if len(related_ids) == 0:
                related_ids = ""

            # loop and generate these dictionaries, store in a list
            d = {"Item Name": item.title, "Author": item.owner, "Sharing": item_share, "Description": item.description, "Item ID": item.id, "Groups": item.shared_with['groups'],
                                "Date Updated": last_edit, "URL": item.url, "Type": item.type, "Folder": fldr_name, "Tags": item.tags, "Categories": item.categories, 
                                "Content Status": item.content_status, "Related Items": related_ids, "Delete Protection": deletion_status, "Transfer Status": xfer}

            dict_list.append(d)
            del d

    generate_report = utils.retry_with_backoff(fn=build_report)
    print(f"Report dataframe built in {timeit.timeit(generate_report)}.")
            
    report_df = pd.DataFrame(dict_list)    
    print("Report generated successfully.")
    report_df
    
    report_df['Project ID'] = np.empty((len(report_df), 0)).tolist()
    graph_view = report_df[['Item ID', 'Related Items']]
    graph_view = graph_view.loc[graph_view['Related Items'] != '']

    graph_data = {}

    for item in range(len(graph_view)):
        graph_data[graph_view.iloc[item]['Item ID']] = list(graph_view.iloc[item]['Related Items'])

    graph_data = utils.remove_none_vals(graph_data)
        
    user_graph = nx.DiGraph(graph_data)
    
    roots = list(utils.topological_sort_grouped(user_graph))[0]

    for root in roots:
        x = str(uuid.uuid4())[:8]
        # filter for root project
        report_df.loc[report_df["Item ID"] == root, "Project ID"] = x
        relates = report_df.loc[report_df['Item ID'] == root]["Related Items"].values[0]
        for item in relates:
            # condition where project ids have already been added 
            report_df.loc[(report_df["Item ID"] == item) & (report_df["Project ID"].str.len() != 0), "Project ID"] = x + ", "
            # condition where a project id does not already exists
            report_df.loc[(report_df["Item ID"] == item) & (report_df["Project ID"].str.len() == 0), "Project ID"] = x
    
    today = date.today()
    today_str = today.strftime("%b-%d-%Y")

    report_name = f"{gis.properties.user.username}_contentReport_{today}.xlsx"

    writer = pd.ExcelWriter(report_name, engine="xlsxwriter")
    report_df.to_excel(writer, sheet_name="Report", startrow=1, header=False)

    workbook = writer.book
    worksheet = writer.sheets['Report']

    # custom header for report following esri style guideline
    header_format = workbook.add_format({'bold': True,
                                        'bottom': 2,
                                        'bg_color': "#C7EAFF"})
    # format for edge items
    edge_format = workbook.add_format({'bg_color': "#BDF2C4"})

    # write the custom header
    for col_num, value in enumerate(report_df.columns.values):
        worksheet.write(0, col_num + 1, value, header_format)


    # change the row background color if item is a 'edge' item, meaning it has no related items or dependencies downstream
    for row in range(len(report_df)):
        if report_df.iloc[row]['Related Items'] == '':
            worksheet.set_row(row + 1, cell_format=edge_format)
            
    worksheet.autofit()
        
    writer.save()

if __name__ == "__main__":
    main()