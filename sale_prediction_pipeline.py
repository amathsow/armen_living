import numpy as np
import pandas as pd
import itertools
import math
import os
import statsmodels.api as sm
import pandas as pd
import re
import matplotlib.pyplot as plt

plt.style.use('fivethirtyeight')
#matplotlib.rcParams['axes.labelsize']=14
#matplotlib.rcParams['xtick.labelsize']=12
#matplotlib.rcParams['ytick.labelsize']=12
#matplotlib.rcParams['text.color']='k'

def plot_trend_item(item_df, column,item_number):
    filtered_data = filter_rows_by_value(item_df, column, item_number)
    #plt.figure(figsize=(20, 8))
    plt.plot(sorted(pd.to_datetime(filtered_data['Posting Date'])), filtered_data['Quantity'],color='r', label='Sale Trend')
    plt.gcf().autofmt_xdate()
    plt.xlabel("Date") 
    plt.ylabel("Quantity Sales") 
    plt.title(f"Quanity sales by item No = {filtered_data.iloc[0]['Item No.']}")
    plt.legend() 

def plot_trend_sales(sales):
    filtered_data = sales
    #plt.figure(figsize=(20, 8))
    plt.plot(sorted(pd.to_datetime(filtered_data['Posting Date'])), filtered_data['Quantity'],color='g', label='Total Sale Trend')
    plt.gcf().autofmt_xdate()
    plt.xlabel("Date") 
    plt.ylabel("Quantity Sales") 
    plt.title("Total sales by day")
    plt.legend() 

def filter_rows_by_value(dataframe, column_name, value):
    """
    Filter rows in a DataFrame based on a particular value in a specified column.

    Parameters:
    - dataframe: pandas DataFrame
        The input DataFrame containing the data.
    - column_name: str
        The name of the column to filter on.
    - value: any
        The value to filter rows on.

    Returns:
    - pandas DataFrame
        A new DataFrame containing only the rows that match the specified value in the specified column.
    """
    # Check if the specified column exists in the DataFrame
    if column_name not in dataframe.columns:
        print(f"Column '{column_name}' not found in the DataFrame.")
        return None

    # Filter rows based on the specified value in the specified column
    filtered_dataframe = dataframe[dataframe[column_name] == value]

    return filtered_dataframe


## take the data and return a dataframe that contain all necessary column for sale prediciton 
def df_preprocess(data_path):
    # foalder of the data
    ##data_path = "./data/inventory/Item Entry Ledger/Item Entry Ledger/"
    path = data_path
    files = os.listdir(path)
    files_xlsx = [f for f in files if f.endswith('.xlsx')]
    mydf_list = []
    for file in files_xlsx:
        mydf = pd.read_excel(os.path.join(path, file),skiprows=2)
        mydf_list.append(mydf)

    df_item = pd.concat(mydf_list)

    df_item['Posting Date'] = pd.to_datetime(df_item['Posting Date'])

    sales = df_item.loc[df_item['Entry Type'] == 'Sale']
    sales['Quantity'] = abs(sales['Quantity'])

    return sales

## function forecast sale by item
def forcaste_sale_by_item(item_df, column,item_number):
    sale_forcast = filter_rows_by_value(item_df, column, item_number)
    sale_forcast = item_df[['Posting Date','Quantity']]
    sale_forcast['Posting Date'] = pd.to_datetime(sale_forcast['Posting Date'])

    #sale_forcast = sale_forcast.groupby("Posting Date")['Quantity'].sum().reset_index()
    sale_forcast.set_index("Posting Date", inplace = True)

    y = sale_forcast["Quantity"].resample('D').mean() #MS mean Month Star
    

    mod = sm.tsa.statespace.SARIMAX(y,
                                order=(1, 1, 1),
                                seasonal_order=(1, 1, 0, 12),
                                enforce_stationarity=False,
                                enforce_invertibility=False)
    results = mod.fit()
    pred_uc = results.get_forecast(steps=100)
    pred_ci = pred_uc.conf_int()
    ax = y.plot(label='observed', figsize=(14, 7))
    pred_uc.predicted_mean.plot(ax=ax, label='Forecast')
    ax.fill_between(pred_ci.index,
                pred_ci.iloc[:, 0],
                pred_ci.iloc[:, 1], color='k', alpha=.25)
    ax.set_xlabel('Date')
    ax.set_ylabel('Furniture Sales')
    #print(pred_ci)
    plt.legend()
    plt.show()  
    return pred_ci    




