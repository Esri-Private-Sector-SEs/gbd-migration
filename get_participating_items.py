from arcgis.gis import GIS
from arcgis.gis import Item

import pandas as pd

def get_participating_items(item: Item, gis: GIS, user: str) -> pd.DataFrame:
    """
    Generates a Pandas dataframe of content participating in item. 
    
    Arguments:
        item (Item): Item which will be searched through for participating content.
        gis (GIS): Active GIS of the item.
        user (User): Owner of the content

    Returns:
        results (Dataframe): Pandas Dataframe of participating content within item.
    """
    
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
    
    item_json = item.get_data(try_json=True)
    flat_keys = flatten_data(item_json)
    
    for k, v in flat_keys.items():
        if "itemId" in k:
            related_itm = gis.content.get(v)
            related_items.append(related_itm)

    for itm in related_items:
        
        d = {"Item Name": itm.title, "Author": item.owner, "Item ID": itm.id, "Type": itm.type, "Tags": item.tags}
        data.append(d)
        
    result = pd.DataFrame(data)
    return result

    

    