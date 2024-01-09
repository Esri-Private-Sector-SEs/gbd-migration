from arcgis.gis import GIS
from arcgis.gis import Item
from datetime import datetime

import pandas as pd
import json
from getpass import getpass

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

def get_participating_items(item: Item, gis: GIS, user: str) -> pd.DataFrame:
    """
    TODO
    """
    
    folders = gis.users.search(user)[0].folders
    
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

    related_items = [] # list of items retrieved from JSON
    data = [] # pandas data
    
    item_json = item.get_data()
    flat_keys = flatten_data(item_json)
    for k, v in flat_keys.items():
        related_items.append(gis.content.get(v))
    
    for itm in related_items:
        # get folders
        for fldr in folders:
            if fldr['id'] == item.ownerFolder:
                fldr_name = fldr['title']
            else:
                fldr_name = 'root'
        
        d = {"Item Name": itm.title, "Author": item.owner, "Item ID": itm.id, "Type": itm.type, "Tags": item.tags, "Folder": fldr_name}
        data.append(d)
        
    result = pd.DataFrame(data)
    return result

    

    