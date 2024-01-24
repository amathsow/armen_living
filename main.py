import numpy as np
import pandas as pd
import itertools
import math
import statsmodels.api as sm
import matplotlib
import warnings
import matplotlib.pyplot as plt
from sale_prediction_pipeline import forcaste_sale_by_item, df_preprocess, filter_rows_by_value, plot_trend_item, plot_trend_sales
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

########################################################

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center;'>Armen living realtime data analysis</h1>", unsafe_allow_html=True)

################# Scatter Chart Logic #################

st.sidebar.markdown("### Filter informaton based on item ID")

item_number = df_sales['Item No.'].unique().tolist()

x_axis = st.sidebar.selectbox("Item number", item_number)



## plot trend sales by item
if x_axis :
    scatter_fig = plt.figure(figsize=(8,4))

    scatter_ax = scatter_fig.add_subplot(111)

    plot_trend_item(df_sales, "Item No.",x_axis)



#sales trend by day:
bar_fig = plt.figure(figsize=(8,4))

bar_ax = bar_fig.add_subplot(111)

plot_trend_sales(df_sales)


## plot stock trend by item
if x_axis:
    hexbin_fig = plt.figure(figsize=(8,4))

    hexbin_ax = hexbin_fig.add_subplot(111)

    plot_trend_item_stock(df_inventory,'Item No.',x_axis)


## plot sales trend by day
if x_axis:
    hist_fig = plt.figure(figsize=(8,4))

    hist_ax = hist_fig.add_subplot(111)

    mean_sales = forcaste_sale_by_item(df_sales,"Item No.",x_axis)


## predit when item will go out of stock
if x_axis:
    item_out_stock = data_item_out_stock(mean_sales, df_inventory,x_axis)


all_item_out_stock = all_item_out_of_stock_day(mean_sales,df_inventory)

##################### Layout Application ##################

container1 = st.container()
col1, col2 = st.columns(2)

with container1:
    with col1:
        scatter_fig
    with col2:
        bar_fig


container2 = st.container()
col3, col4 = st.columns(2)

with container2:
    with col3:
        hexbin_fig
    with col4:
        hist_fig


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
    st.markdown(html_str1, unsafe_allow_html=True)
    st.dataframe(all_item_out_stock,use_container_width=True)


