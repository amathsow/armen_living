import numpy as np
import pandas as pd
import itertools
import math
import os
import streamlit as st
import datetime
import statsmodels.api as sm
#from prettytable import PrettyTable
import pandas as pd
import re
import heapq
import plotly.express as px
import matplotlib.pyplot as plt
from sale_prediction_pipeline import filter_rows_by_value
plt.style.use('fivethirtyeight')
#matplotlib.rcParams['axes.labelsize']=14
#matplotlib.rcParams['xtick.labelsize']=12
#matplotlib.rcParams['ytick.labelsize']=12
#matplotlib.rcParams['text.color']='k'



def extract_date_from_excel_filename(filename):
    # Define a regular expression pattern to match the date in the filename
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    
    # Use the re.search function to find the date in the filename
    match = re.search(date_pattern, filename)
    
    if match:
        # Extract the matched date and return it
        date_str = match.group()
        return date_str
    else:
        # If no date is found, return None or raise an exception, depending on your needs
        return None

# Example usage:
filename = "Item List KHOFFMAN 2023-10-02T15_43_14.xlsx"
date = extract_date_from_excel_filename(filename)
if date:
    print("Extracted date:", date)
else:
    print("No date found in the filename.")


def get_data_inventory(path):
    # AMP100 - OH All foalder
    #path = "./data/inventory/Item Entry Ledger/Item Entry Ledger/"
    files = os.listdir(path)
    files_xlsx = [f for f in files if f.endswith('.xlsx')]
    mydf_list = []
    for file in files_xlsx:
        mydf = pd.read_excel(os.path.join(path, file),skiprows=2)
        mydf_list.append(mydf)

    df_item = pd.concat(mydf_list)
    return df_item

def plot_trend_item_stock(item_df, column,item_number):
    filtered_data = filter_rows_by_value(item_df, column, item_number)
    filtered_data['Date']= pd.to_datetime(filtered_data['Date'])
    
    #plt.figure(figsize=(20, 8))
    fig1 = px.line(filtered_data,sorted(filtered_data['Date']), filtered_data['Quantity on Hand'])
    #plt.gcf().autofmt_xdate()
    #plt.xlabel("Date") 
    #plt.ylabel("Quantity On Hand Available") 
    #plt.title(f"Quantity On Hand Available by item No = {filtered_data.iloc[0]['Item No.']}")
    #plt.legend() 
    fig1.update_traces(line_color='#dc6b3c', line_width=5)
    return fig1
    

def data_item_out_stock1(sales,df_stock, item):
    data_stock = df_stock[['Item No.', 'Quantity on Hand']]
    filtered_data = filter_rows_by_value(data_stock, 'Item No.', item)
    sales["sum"] = sales['yhat'].cumsum().round()
    total_quantity_item1 = filtered_data.iloc[0]['Quantity on Hand']
    if total_quantity_item1 <= 0: 
        return f"The item {item} is out of stock"
    else:
        total_quantity_item= heapq.nsmallest(1, list(sales["sum"]), key=lambda x: abs(x-total_quantity_item1))[0]
        if total_quantity_item<max(sales["sum"]):
            item_out_stock = filter_rows_by_value(sales, 'sum', total_quantity_item)
        
            ## print time when the item will go out of stock in the week
            Date_out_stock = item_out_stock['ds'].iloc[0]
            return Date_out_stock.date()
        else:
            return "Item wont be out of stock during the week"
    
def data_item_out_stock(sales,df_stock, item):
    data_stock = df_stock[['Item No.', 'Quantity on Hand']]
    filtered_data = filter_rows_by_value(data_stock, 'Item No.', item)
    sales["sum"] = sales['yhat'].cumsum().round()
    total_quantity_item = filtered_data.iloc[0]['Quantity on Hand']
    if total_quantity_item <= 0: 
        return f"The item {item} is already out of stock"
    else:
        #total_quantity_item= heapq.nsmallest(1, list(sales["sum"]), key=lambda x: abs(x-total_quantity_item1))[0]
        if total_quantity_item<max(sales["sum"]):
            #result = f"the item {item} will be out of stock during the week {sales['ds'].iloc[0]}"
            return "okay"
        else:
            result = f"The item {item} wont be out of stock during the week {sales['ds'].iloc[0]}"
            return result   


@st.cache_data
def all_item_out_of_stock_day(mean_sales,sales,df_item):
    global results
    df_item = df_item[['Item No.', 'Quantity on Hand']]
    
    results = {}
    for item in df_item['Item No.'].unique():
        row_sales_item = filter_rows_by_value(sales, 'Item No.', item)
        result = data_item_out_stock(mean_sales,df_item, item)
        if result=="okay" and len(row_sales_item)>=2:
            filtered_data = filter_rows_by_value(df_item, 'Item No.', item)
            value = filtered_data.iloc[0]['Quantity on Hand']
            if value in results:
                results[value].append(item)
            else:
                results[value] = [item] 

    results = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in results.items() ]))
    #print(result)
    # Find the maximum length among all values
    #max_length = max(len(v) if isinstance(v, list) else 1 for v in results.values())

    # Pad the lists with empty strings to make them of equal length
    #for key, value in results.items():
    #    if isinstance(value, list):
    #        results[key] += [''] * (max_length - len(value))

    # Create a PrettyTable
    #table = PrettyTable(result.keys())

    # Add rows to the table
    #for i in range(max_length):
    #    table.add_row([result[key][i] for key in result.keys()])

    # Display the table
    return results 
    
