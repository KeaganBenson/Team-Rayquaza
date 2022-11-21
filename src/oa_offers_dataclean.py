import re

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("ggplot")
plt.rcParams["figure.figsize"] = (5,3)

PATH_FOLDER = "..\\data\\raw"

FILENAME_OA_OFFERS = "offer_acceptance_offers.csv"
PATH_FILE_OA_OFFERS = os.path.join(PATH_FOLDER, FILENAME_OA_OFFERS)
oa_offers_orig = pd.read_csv(PATH_FILE_OA_OFFERS)
oa_offers = oa_offers_orig

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
    '''
    output = ln(column+1)
    '''
    return column.apply(np.log1p)
def add_logged_column(df, column_name):
    column = df[column_name]
    logged_column = get_log(column)
    df["LOG({0})".format(column_name)] = logged_column
    return df


# In[ ]:
def dataclean(oa_offers):

    bool_column_names = ['SELF_SERVE', 'IS_OFFER_APPROVED',
           'AUTOMATICALLY_APPROVED', 'MANUALLY_APPROVED', 'WAS_EVER_UNCOVERED',
           'COVERING_OFFER', 'LOAD_DELIVERED_FROM_OFFER', 'RECOMMENDED_LOAD', 'VALID']
    categorical_column_names = ["OFFER_TYPE"]
    numerical_column_names = ["RATE_USD"]

    # convert all boolean columns to a numerical datatype
    oa_offers_bool_to_num_columns = (oa_offers.loc[:,bool_column_names]).astype(float)
    oa_offers.loc[:,bool_column_names] = oa_offers_bool_to_num_columns
    


    # convert date columns to datetime columns
    datetime_created_on_hq_column = pd.to_datetime(oa_offers["CREATED_ON_HQ"])
    oa_offers["CREATED_ON_HQ"] = datetime_created_on_hq_column



    oa_offers = add_logged_column(oa_offers,"RATE_USD")



    is_pooled_or_gate_column = (
        (oa_offers["OFFER_TYPE"]=="pool") | ((oa_offers["REFERENCE_NUMBER"].str.count(",")+1)>1)
    ).astype(float)
    # Matt said there are 2 ways an offer can be determined as pooled: if the OFFER_TYPE column == pool,
    # and a second method that makes sure that the REFERENCE column has 2 or more references in it.
    # For insurance, this column tells if an offer is pooled or not using BOTH methods, (as an OR-gate statement)
    oa_offers["IS_POOLED_OR_GATE"] = is_pooled_or_gate_column


    # a column that denotes the number of offers that an order has received.
    offers_amount_column = groupby_transform_value_count(oa_offers[["REFERENCE_NUMBER"]])
    oa_offers["OFFER_AMOUNT"] = offers_amount_column



    # cleans the raw reference column from a string to a list of strings
    reference_numbers_column = oa_offers["REFERENCE_NUMBER"].values
    reference_number_column = get_list_of_reference_numbers(oa_offers["REFERENCE_NUMBER"])
    oa_offers["REFERENCE_NUMBERS"] = reference_numbers_column
    oa_offers["REFERENCE_NUMBER"] = reference_number_column


    # explodes the reference list.
    # The OFFER_AMOUNT column MUST BE created before this action
    oa_offers = oa_offers.explode("REFERENCE_NUMBER")

    return oa_offers

