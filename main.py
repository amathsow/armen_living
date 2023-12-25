from logging.handlers import MemoryHandler
import numpy as np
import pandas as pd
import itertools
import math
import statsmodels.api as sm
import matplotlib
import warnings
import matplotlib.pyplot as plt
from sale_prediction_pipeline import forcaste_sale_by_item, df_preprocess, filter_rows_by_value, plot_trend_item, plot_trend_sales,price_sale_item,forcaste_sale_prophet_item
from item_pipeline import get_data_inventory,plot_trend_item_stock, data_item_out_stock, all_item_out_of_stock_day
warnings.filterwarnings("ignore")
plt.style.use('fivethirtyeight')
matplotlib.rcParams['axes.labelsize']=14
matplotlib.rcParams['xtick.labelsize']=12
matplotlib.rcParams['ytick.labelsize']=12
matplotlib.rcParams['text.color']='k'
import streamlit as st
####### Load Dataset #####################


## data gathering
#df_sales = df_preprocess("./data/inventory/Item Entry Ledger/Item Entry Ledger/")
df_sales = pd.read_csv("sale.csv")
#df_inventory = get_data_inventory("./data/inventory/Item Entry Ledger/Item Entry Ledger/")
df_inventory = pd.read_csv("inventory.csv")
# dataframe that contain all item with unit price
price_sale=pd.read_excel('./data/Armen Living 2023 Sales.xlsx')

########################################################

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center;'>Armen living realtime data analysis</h1>", unsafe_allow_html=True)

################# Scatter Chart Logic #################

st.sidebar.markdown("### Filter informaton based on item ID")

item_number = df_sales['Item No.'].unique().tolist()

x_axis = st.sidebar.selectbox("Item number", item_number)
button = st.sidebar.button("All item out of stock", type="primary")



## plot trend sales by item
if x_axis :
    scatter_fig = plt.figure(figsize=(8,4))

    scatter_ax = scatter_fig.add_subplot(111)

    fig2 = plot_trend_item(df_sales, "Item No.",x_axis)



#sales trend by day:
bar_fig = plt.figure(figsize=(8,4))

bar_ax = bar_fig.add_subplot(111)

fig3 = plot_trend_sales(df_sales)


## plot stock trend by item
if x_axis:
    hexbin_fig = plt.figure(figsize=(8,4))

    hexbin_ax = hexbin_fig.add_subplot(111)

    fig1 = plot_trend_item_stock(df_inventory,'Item No.',x_axis)


## plot sales trend by day
if x_axis:
    hist_fig = plt.figure(figsize=(8,4))

    hist_ax = hist_fig.add_subplot(111)
    mean_sales,fig = forcaste_sale_prophet_item(df_sales,"Item No.",x_axis)
    if not isinstance(mean_sales, str):
        #mean_sales = forcaste_sale_by_item(df_sales,"Item No.",x_axis)
        mean_sales = pd.DataFrame(mean_sales)
        mean_sales = mean_sales[:1]
        #st.write(mean_sales)



## predit when item will go out of stock
if x_axis:
    if not mean_sales.empty:
        item_out_stock = data_item_out_stock(mean_sales, df_inventory,x_axis)
        if item_out_stock=="okay":
            item_out_stock = f"the item {x_axis} has {mean_sales['yhat'].iloc[0].round()} and will be out of stock during the week {mean_sales['ds'].iloc[0]}"


#all_item_out_stock = all_item_out_of_stock_day(mean_sales,df_inventory)

if button and 'executed_flag' not in st.session_state:

    week_sales = mean_sales['yhat'].iloc[0].round()
    price_sale_item = price_sale_item(price_sale,x_axis)

    all_item_out_stock = all_item_out_of_stock_day(mean_sales,df_sales,df_inventory)
    #st.session_state.executed_flag = True
    container0 = st.container()
    col1, col2 = st.columns(2)
    with container0:
        with col1:
            col1.metric(str(mean_sales['ds'].iloc[0]),"Total weekly sales", week_sales)
        with col2:
            col2.metric(x_axis, "Revenue", price_sale_item*week_sales)



##################### Layout Application ##################

container1 = st.container()
col1, col2 = st.columns(2)



with container1:
    with col1:
        #scatter_fig
        fig2.update_layout(
              title= f'Sales Trend for Item: {x_axis}',
              xaxis_title='Date',
              yaxis_title='Quantity sales',
              )
        fig1.update_traces(marker_color='rgb(100,50,40)')
        st.plotly_chart(fig2,use_container_width=True)
        
    with col2:
        #bar_fig
        fig3.update_layout(
              title= 'Total sales Trend by day',
              xaxis_title='Date',
              yaxis_title='Quantity sales',
              )
        fig3.update_traces(marker_color='rgb(50,100,100)')
        st.plotly_chart(fig3,use_container_width=True)


container2 = st.container()
col3, col4 = st.columns(2)

with container2:
    with col3:
        #hexbin_fig
        fig1.update_layout(
              title= f'Stock Trend by Item: {x_axis}',
              xaxis_title='Date',
              yaxis_title='Quantity on Hand',
              )
        fig1.update_traces(marker_color='rgb(100,100,100)')
        st.plotly_chart(fig1,use_container_width=True)
    with col4:
        #hist_fig
        fig.update_layout(
              title='Sales Forecasting by Item',
              xaxis_title='Date',
              yaxis_title='Quantity sold by item',
              )
        st.plotly_chart(fig,use_container_width=True)


if button:
    container3 = st.container()
    col5, col6 = st.columns(2)

    ## display when an item will go out of stock

    html_str = f"""
    <style>
    p.a {{
    font: bold 20px Courier;
    color: green;   
    }}
    </style>
    <p class="a">{item_out_stock}</p>
    """

   
    ## display all item out of stock by day during the week
    html_str1 = f"""
    <style>
    p.a {{
    font: bold 20px Courier;
    color: green;
    }}
    </style>
    <p class="a">All items out of stock by day during the week</p>
    """
    with container3:
        with col5:
            st.markdown(html_str, unsafe_allow_html=True)
            #mean_sales.drop(['yhat_lower', 'yhat_upper', 'sum'], axis=1)
            st.dataframe(mean_sales,use_container_width=True)
        with col6:

            st.markdown(html_str1, unsafe_allow_html=True)
            st.dataframe(all_item_out_stock)


