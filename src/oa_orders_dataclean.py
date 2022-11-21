import re

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("ggplot")
plt.rcParams["figure.figsize"] = (5,3)

PATH_FOLDER = "..\\data\\raw"

FILENAME_OA_ORDERS = "offer_acceptance_orders.csv"
PATH_FILE_OA_ORDERS = os.path.join(PATH_FOLDER, FILENAME_OA_ORDERS)
oa_orders_orig = pd.read_csv(PATH_FILE_OA_ORDERS)
oa_orders = oa_orders_orig

# In[7]:


def groupby_transform_value_count(df_column):
    '''
    shows the group-size of a group that a row belongs to.
    this is supposed to be faster than df_column.groupby(column).transform(lambda series: len(series))
    Args:
        df_column (pd.DataFrame): this is a dataframe with 1 (categorical) column, NOT a pd.Series
    Returns:
        pd.Series: a pd.series with the same # of rows as df_column. each row has their respective group's groupsize. So there's many duplicate numbers
    '''
    column_name = list(df_column.columns)[0]
    temp_counter = df_column[column_name].value_counts()
    temp_counter = temp_counter.reset_index().rename(columns={"index":column_name,column_name:"count"})
    df_column = df_column.merge(temp_counter,on=[column_name])
    return df_column["count"]
def dataclean_ftl_duplicate_references(oa):
    '''
    Part of a greater data cleaning on removing incorrect FTL labels,
    Removes FTL rows that have reference numbers that show up more than once, as those rows are incorrectly labeled FTL
    '''
    assert "TRANSPORT_MODE" in oa.columns
    assert "REFERENCE_NUMBER" in oa.columns
    oa_ftl = oa[oa["TRANSPORT_MODE"]=="FTL"]
    temp_counter = oa_ftl["REFERENCE_NUMBER"].value_counts()
    temp_counter = temp_counter.reset_index().rename(columns={"index":"REFERENCE_NUMBER","REFERENCE_NUMBER":"count"})
    oa_ftl_counted = oa_ftl.merge(temp_counter,on=["REFERENCE_NUMBER"])
    oa_ftl_duplicate_reference_numbers = oa_ftl_counted[oa_ftl_counted["count"]>1]
    oa = oa.drop(list(oa_ftl_duplicate_reference_numbers.index), axis=0)    
    return oa

def dataclean_ftl_nonquote(oa):
    '''
    Part of a greater data cleaning on removing incorrect FTL labels,
    Removes FTL rows that don't have quote as the transport mode
    '''
    assert "OFFER_TYPE" in oa.columns
    assert "TRANSPORT_MODE" in oa.columns    
    oa = oa[~((oa["TRANSPORT_MODE"]=="FTL") & (oa["OFFER_TYPE"]!="quote"))]
    return oa


def get_list_of_reference_numbers(column):
    '''
    cleans the raw reference column from a string to a list of strings
    '''
    result = (column
    ).str.replace("\n"," "
    ).str.replace(" ",""
    ).str.replace('''"''',''
    ).str.replace("[",""
    ).str.replace("]",""
    ).str.split(",")
    return result


def get_log(column): 
    return column.apply(np.log1p)
def add_logged_column(df, column_name):
    logged_column = get_log(df[column_name])
    df["LOG({0})".format(column_name)] = logged_column
    return df

def dataclean(oa_orders):


    bool_column_names = ['FD_ENABLED', 'EXCLUSIVE_USE_REQUESTED','HAZARDOUS', 
                         'REEFER_ALLOWED', 'STRAIGHT_TRUCK_ALLOWED','LOAD_TO_RIDE_REQUESTED']
    numerical_column_names = ["ESTIMATED_COST_AT_ORDER",
                              "APPROXIMATE_DRIVING_ROUTE_MILEAGE",
                              "PALLETIZED_LINEAR_FEET",
                              "LOAD_BAR_COUNT"]
    categorical_column_names = ["DELIVERY_TIME_CONSTRAINT","TRANSPORT_MODE"]

    # convert all boolean columns to a numerical datatype
    oa_orders_bool_to_num_columns = (oa_orders.loc[:,bool_column_names]).astype(float)
    oa_orders.loc[:,bool_column_names] = oa_orders_bool_to_num_columns
    
    # Matt said that any duplicate references is likely an error
    oa_orders = dataclean_ftl_duplicate_references(oa_orders)

    # convert to datetime
    oa_orders["ORDER_DATETIME_PST"] = pd.to_datetime(oa_orders["ORDER_DATETIME_PST"])
    oa_orders["PICKUP_DEADLINE_PST"] = pd.to_datetime(oa_orders["PICKUP_DEADLINE_PST"])


    # add logged versions of these columns
    oa_orders = add_logged_column(oa_orders,"ESTIMATED_COST_AT_ORDER")
    oa_orders = add_logged_column(oa_orders,"APPROXIMATE_DRIVING_ROUTE_MILEAGE")
    oa_orders = add_logged_column(oa_orders,"PALLETIZED_LINEAR_FEET")
    oa_orders = add_logged_column(oa_orders,"LOAD_BAR_COUNT")



    # add the time between order and deadline as a column. And also add a logged version of it.
    time_between_order_and_deadline_column = (
        pd.to_datetime(oa_orders["PICKUP_DEADLINE_PST"]) - pd.to_datetime(oa_orders["ORDER_DATETIME_PST"])
    )
    seconds_between_order_and_deadline_column = (
     time_between_order_and_deadline_column / np.timedelta64(1, 's')
    )
    oa_orders["SECONDS_BETWEEN_ORDER_AND_DEADLINE"] = seconds_between_order_and_deadline_column
    oa_orders = add_logged_column(oa_orders,"SECONDS_BETWEEN_ORDER_AND_DEADLINE")

    
    reference_numbers_column = oa_orders["REFERENCE_NUMBER"].values
    oa_orders["ORDER_REFERENCE_NUMBERS"] = reference_numbers_column
    reference_number_column = get_list_of_reference_numbers(oa_orders["REFERENCE_NUMBER"])
    oa_orders["REFERENCE_NUMBER"] = reference_number_column

    assert oa_orders["ORDER_REFERENCE_NUMBERS"].str.count(",").sum()==0


    # explodes the reference list.
    # This is somewhat pointless since for this table, REFERENCE_NUMBER should have lists with only 1 reference number.
    oa_orders = oa_orders.explode("REFERENCE_NUMBER")


    return oa_orders


