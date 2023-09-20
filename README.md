# GBD Migration Project

There are 3 files in this repository:

1. **Content Migration Notebook**. A tool to perform AGOL to AGOL transfers on single items in an organization.
2. **Content Report Notebook**. A tool to generate a report of all content owned by a user, alongside essential information associated with the item.
3. **Catalog**. A functional csv essential to use with the Content Migration notebook. Records transfers in real time for administrative logging purposes. 

## Content Migration Notebook

This notebook is used to do AGOL to AGOL transfers, designed to handle one item at a time. In AGOL to AGOL transfers, we refer to the org with the original content as the **origin portal**. The AGOL where we want to transfer our items to is the **destination portal.**

### Installation 
  1. Download the latest version from Github.
  2. Log into the ArcGIS online organization *where you want your items to be transferred **to*** (the destination portal).
  3. Add the file as an item to your ArcGIS Online organization. When prompted to select a Python Notebook version, use the Basic. Advanced is not needed for this tool.
  4. Upload the catalog.csv file to your ArcGIS Online organization as an item:
     
     a. For "How would you like to add this file?", select Add catalog.csv and create a hosted feature layer or table.
     
     b. Leave the fields default.
     
     c. Click the Addresses or place names drop down menu at the top of the Location settings panel. Select None.
     
     d. Click save. Go to the Item page, grab its Item ID and save it for use later.
     
  6. Open the Item and proceed to configuration.

### Configuration
  1. **CATALOG_ID**: Item ID for the catalog csv you uploaded to the destination portal.
  2. **ORIGIN_TRANSFER_USER**: Username of the transfer user, an administrator in the origin portal.
  3. **ORIGIN_URL**: URL of the origin portal.
  4. **ITEM_ID**: The Item ID in the original portal for the item you want to transfer.

 After configuration, you can simply execute each cell and the script should handle the rest!

 ## Content Report Notebook

 This notebook is a companion to the content migration tool, creating an inventory of a user's content. See the documentation at the top of the notebook for more information on how to use it. 

 ### Installation
  1. Download the latest version from Github.
  2. Log into your ArcGIS online organization *where you want to transfer items **from*** (the origin portal).
  3. Add the file as an item to your ArcGIS Online organization. When prompted to select a Python Notebook version, use the Basic. Advanced is not needed for this tool.

 
