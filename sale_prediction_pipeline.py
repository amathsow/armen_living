import numpy as np
import pandas as pd
import itertools
import math
import os
import statsmodels.api as sm
import pandas as pd
import plotly.express as px
import re
import matplotlib.pyplot as plt
import plotly.express as px
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.offline as py

plt.style.use('fivethirtyeight')
#matplotlib.rcParams['axes.labelsize']=14
#matplotlib.rcParams['xtick.labelsize']=12
#matplotlib.rcParams['ytick.labelsize']=12
#matplotlib.rcParams['text.color']='k'

def plot_trend_item(item_df, column,item_number):
    filtered_data = filter_rows_by_value(item_df, column, item_number)
    filtered_data['Posting Date']= pd.to_datetime(filtered_data['Posting Date'])
    filtered_data = filtered_data.groupby("Posting Date")['Quantity'].sum().reset_index()
    filtered_data.set_index("Posting Date", inplace = True)
    filtered_data = filtered_data["Quantity"].resample('M').sum()
    filtered_data = filtered_data.reset_index()
    #plt.figure(figsize=(20, 8))
    fig = px.line(filtered_data,sorted(pd.to_datetime(filtered_data['Posting Date'])), filtered_data['Quantity'])
    #plt.gcf().autofmt_xdate()
    #plt.xlabel("Date") 
    #plt.ylabel("Quantity Sales") 
    #plt.title(f"Quanity sales by item No = {filtered_data.iloc[0]['Item No.']}")
    #plt.legend()
    fig.update_traces(line_color='#4c963c', line_width=3)
    return fig 

def plot_trend_sales(sales):
    filtered_data = sales
    filtered_data['Posting Date']= pd.to_datetime(filtered_data['Posting Date'])
    filtered_data = filtered_data.groupby("Posting Date")['Quantity'].sum().reset_index()
    filtered_data.set_index("Posting Date", inplace = True)
    filtered_data = filtered_data["Quantity"].resample('M').sum()
    filtered_data = filtered_data.reset_index()
    #plt.figure(figsize=(20, 8))
    fig = px.line(filtered_data,pd.to_datetime(filtered_data['Posting Date']), filtered_data['Quantity'])
    fig.update_traces(line_color='#42b5bd', line_width=3)
    #plt.gcf().autofmt_xdate()
    #plt.xlabel("Date") 
    #plt.ylabel("Quantity Sales") 
    #plt.title("Total sales by day")
    #plt.legend() 
    return fig

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

## income after sale by item
def price_sale_item(price_sale,item):
    price_sale = price_sale[['No.','Unit Price']]
    price_sale = filter_rows_by_value(price_sale, 'No.', item)
    return price_sale['Unit Price'].values[0]

## function forecast sale by item
def forcaste_sale_by_item(item_df, column,item_number):
    sale_forcast = filter_rows_by_value(item_df, column, item_number)
    sale_forcast = sale_forcast[['Posting Date','Quantity']]
    sale_forcast['Posting Date'] = pd.to_datetime(sale_forcast['Posting Date'])

    #sale_forcast = sale_forcast.groupby("Posting Date")['Quantity'].sum().reset_index()
    sale_forcast.set_index("Posting Date", inplace = True)

    y = sale_forcast["Quantity"].resample('D').sum() #MS mean Month Star
    

    mod = sm.tsa.statespace.SARIMAX(y,
                                order=(0, 1, 0),
                                seasonal_order=(0, 0, 0, 0),
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


## function forecast sale by item
def forcaste_sale_prophet_item(sales, column,item_number):
    sale_forcast = filter_rows_by_value(sales, column, item_number)
    sale_forcast = sale_forcast[['Posting Date','Quantity']]
    sale_forcast['Posting Date'] = pd.to_datetime(sale_forcast['Posting Date'])
    if sale_forcast.empty or len(sale_forcast)==1:
        result = f"The item is out of stock, there is no trend data to predict sales"
        return result, False
    else:
        sale_forcast = sale_forcast.groupby("Posting Date")['Quantity'].sum().reset_index()
        sale_forcast.set_index("Posting Date", inplace = True)
        y = sale_forcast["Quantity"].resample('M').sum()
        y = y.reset_index()
        print(y)

        sale_forcast = y.rename(columns={'Posting Date': 'ds','Quantity': 'y'})
    
        my_model = Prophet()
        my_model.fit(sale_forcast)
        future_dates = my_model.make_future_dataframe(periods=3, freq='M')
        #future_dates = pd.DataFrame({'ds':['2023-12-06','2023-12-07','2023-12-08','2023-12-09','2023-12-10','2023-12-11','2023-12-12']})
        forecast = my_model.predict(future_dates)
        fig = plot_plotly(my_model, forecast) # This returns a plotly Figure
        #py.iplot(fig)
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        result = result.sort_values(by='ds',ascending=True)
        mask = (result['ds'] >= '2023-12-08 00:00:00' )
        #mask = (result['ds'] > '2023-12-05 00:00:00') & (result['ds'] <= '2023-12-30 00:00:00')
        final = result.loc[mask]
        return final, fig
    
      
    
      
    
      


