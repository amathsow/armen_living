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
from sale_prediction_pipeline import filter_rows_by_value,forcaste_sale_prophet_item, forcaste_sale_prophet_item1
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
    filtered_data = filtered_data.groupby("Date")['Quantity on Hand'].sum().reset_index()
    filtered_data.set_index("Date", inplace = True)
    filtered_data = filtered_data["Quantity on Hand"].resample('M').sum()
    filtered_data = filtered_data.reset_index()
    
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
    #sales = pd.DataFrame(sales)
    data_stock = df_stock[['Item No.', 'Quantity on Hand']]
    filtered_data = filter_rows_by_value(data_stock, 'Item No.', item)
    #print("sales",sales)
    if not isinstance(sales, str) and  not sales.empty:
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
                result = f"The item {item} wont be out of stock during the week {sales['ds'].iloc[0]} and there are {total_quantity_item} item available"
                return result 


@st.cache_data
def all_item_out_of_stock_day(sales,df_item):
    df_item = df_item[['Item No.', 'Quantity on Hand']]
    results = {}
    sales['Posting Date'] = pd.to_datetime(sales['Posting Date'])
    # Group by 'item No' and the month of the 'date'
    grouped_sales = sales.groupby(['Item No.', sales['Posting Date'].dt.month])
    # Filter items with at least 2 rows per month
    filtered_df = grouped_sales.filter(lambda x: len(x) >= 10)
    nb_items = filtered_df['Item No.'].unique()
    
    for item in nb_items[:100]:
        mean_sales= forcaste_sale_prophet_item1(sales,"Item No.",item)
        if not isinstance(mean_sales, str):
            mean_sales = pd.DataFrame(mean_sales)
            print("mean_sales",mean_sales)
            mean_sales = mean_sales[:1]
            row_sales_item = filter_rows_by_value(sales, 'Item No.', item)
            result = data_item_out_stock(mean_sales,df_item, item)
            if result=="okay" and len(row_sales_item)>=2:
                filtered_data = filter_rows_by_value(df_item, 'Item No.', item)
                value = filtered_data.iloc[0]['Quantity on Hand']
                if value in results:
                    results[item].append([value,mean_sales['ds'].iloc[0],mean_sales['yhat'].iloc[0],mean_sales['yhat_lower'].iloc[0],mean_sales['yhat_upper'].iloc[0]])
                else:
                    results[item] = [value,mean_sales['ds'].iloc[0],mean_sales['yhat'].iloc[0],mean_sales['yhat_lower'].iloc[0],mean_sales['yhat_upper'].iloc[0]] 

    # Create an empty DataFrame with desired columns
    df = pd.DataFrame(columns=["item_number","Date" ,"Quantity on stock", "Sale Pred", "Min Sale Pred","Max Sale Pred"])

    # Iterate over the dictionary items and add rows to the DataFrame
    for key, values in results.items():
        if len(values) == 5:  # Assuming each list has quantity stock, sales pred, max and min sales pred
            df = df.append({'item_number': key,'Date': values[1] ,'Quantity on stock': values[0], 'Sale Pred': values[2], 'Min Sale Pred': values[3],'Max Sale Pred': values[4] }, ignore_index=True)

    return df
    
