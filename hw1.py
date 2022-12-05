#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from datetime import datetime
import itertools
import math
import random


import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import numpy as np


# In[2]:


data = pd.read_csv("offer_acceptance_offers.csv")
def conv_time(string):
    datetime_object = datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    return datetime_object

data['CREATED_ON_HQ'] = data['CREATED_ON_HQ'].apply(conv_time)
data.head()


# ## Cleaning of DataFrames (working on only FTL types)

# In[3]:


FTL_data = data[data['TRANSPORT_MODE'] == 'FTL']
FTL_data = FTL_data.drop(['IS_OFFER_APPROVED', 'AUTOMATICALLY_APPROVED', 'MANUALLY_APPROVED'], axis=1)
FTL_data.shape


# In[4]:


orders = pd.read_csv("offer_acceptance_orders.csv")
orders['ORDER_DATETIME_PST'] = orders['ORDER_DATETIME_PST'].apply(conv_time)
orders['PICKUP_DEADLINE_PST'] = orders['PICKUP_DEADLINE_PST'].apply(conv_time)

orders['diff_ORDER_PICKUP_DEADLINE'] = (orders['PICKUP_DEADLINE_PST'] - orders['ORDER_DATETIME_PST'])
orders.head()


# In[ ]:





# In[5]:


joined = pd.merge(FTL_data, orders, on='REFERENCE_NUMBER', how='inner')
joined.sort_values(by = ['REFERENCE_NUMBER', 'CREATED_ON_HQ'], ascending = [True, True], na_position = 'first')
joined = joined[joined['OFFER_TYPE'] == 'quote']
joined


# In[6]:


# fill driving distance with mean of in zip code results, most na were in zip code
same = orders[orders['ORIGIN_3DIGIT_ZIP'] ==  orders['DESTINATION_3DIGIT_ZIP']]
mean_same_distance = same['APPROXIMATE_DRIVING_ROUTE_MILEAGE'].dropna().mean()
orders['APPROXIMATE_DRIVING_ROUTE_MILEAGE'] = orders['APPROXIMATE_DRIVING_ROUTE_MILEAGE'].fillna(mean_same_distance)

# fill FD enabled with false
orders['FD_ENABLED'] = orders['FD_ENABLED'].fillna(False)

# drop everything else, cause all had consistance NA 7
# 18 in Transportmode
# change all boolean data back to boolean
containsNa = (orders.isnull().sum() > 1).to_dict()
orders = orders.dropna()
for key,value in containsNa.items():
    if value:
        if orders[key].unique().sum() == 1:
            orders[key] = orders[key].astype(bool)


# In[7]:


offers = pd.read_csv("offer_acceptance_offers.csv",low_memory=False)
offers.head()


# In[8]:


s = offers.groupby('REFERENCE_NUMBER').count()['CARRIER_ID']
nOffers_rec = s[s < 15]


# In[9]:


ftl = orders[orders['TRANSPORT_MODE'] == 'FTL']
ftl.set_index('REFERENCE_NUMBER',inplace = True)
joinedDF = ftl.join(nOffers_rec,how = 'left')
joinedDF['NUMBER_OFFERS'] = joinedDF['CARRIER_ID'].fillna(0)
joinedDF.drop('CARRIER_ID',axis = 1,inplace = True)
joinedDF['SECONDS_BETWEEN_ORDER_AND_DEADLINE'] = joinedDF['diff_ORDER_PICKUP_DEADLINE'].dt.total_seconds()
joinedDF


# In[10]:


# variables used for modeling
bool_column_names = [
 'FD_ENABLED',
 'EXCLUSIVE_USE_REQUESTED',
 'HAZARDOUS',
 'REEFER_ALLOWED',
 'STRAIGHT_TRUCK_ALLOWED',
 'LOAD_TO_RIDE_REQUESTED',
]

numerical_loggable_column_names = [
 'APPROXIMATE_DRIVING_ROUTE_MILEAGE',
 'PALLETIZED_LINEAR_FEET',
 'SECONDS_BETWEEN_ORDER_AND_DEADLINE',
 'LOAD_BAR_COUNT',
 'ESTIMATED_COST_AT_ORDER'
]


# In[11]:


train=joinedDF.sample(frac=0.8,random_state=200)
test=joinedDF.drop(train.index)


# In[12]:


xTrain = train[bool_column_names + numerical_loggable_column_names].to_numpy()
yTrain = train['NUMBER_OFFERS'].to_numpy()
xTest = test[bool_column_names + numerical_loggable_column_names].to_numpy()
yTest = test['NUMBER_OFFERS'].to_numpy()
xTrain


# In[13]:


reg = LinearRegression().fit(xTrain, yTrain)
preds = reg.predict(xTest).round()
mean_absolute_error(yTest,preds)


# In[14]:


pd.Series(preds).value_counts()


# In[15]:


avg_pred = [np.mean(nOffers_rec)] * len(yTest)
mean_absolute_error(yTest,avg_pred)


# In[16]:


test


# In[17]:


len(preds)


# In[18]:


offers_orders = pd.merge(test, orders, on='REFERENCE_NUMBER', how='inner')
offers_orders['Estimated_Num_offers'] = preds.astype(int)
offers_orders = offers_orders.set_index('REFERENCE_NUMBER')

offers_orders


# In[19]:


joinedTable = test.join(offers.set_index('REFERENCE_NUMBER').drop(columns = ['TRANSPORT_MODE']), how = 'inner')
joinedTable


# In[20]:


nonidx_joinedDf = joinedTable.reset_index()
nonidx_joinedDf['ESTIMATED_COST_AT_ORDER']

uniqueRefs = nonidx_joinedDf['REFERENCE_NUMBER'].unique()
uniqueRefs


# In[21]:


train, test = train_test_split(nonidx_joinedDf, test_size=0.2)
y = np.array(train['RATE_USD'])
X = np.array(train[['SECONDS_BETWEEN_ORDER_AND_DEADLINE','ESTIMATED_COST_AT_ORDER']])
reg = LinearRegression().fit(X, y)
predictions = reg.predict(nonidx_joinedDf[['SECONDS_BETWEEN_ORDER_AND_DEADLINE','ESTIMATED_COST_AT_ORDER']])
predictions


# In[22]:


nonidx_joinedDf['My_ESTIMATED_COST_AT_ORDER'] = predictions
nonidx_joinedDf


# In[23]:


len(uniqueRefs)


# ## Conduct Sec Method with a prior using model that estimates the # of offers and a model that estimates cost

# In[25]:


rates = []
costs = []

for i in uniqueRefs:
    Estimated_Num_offers = offers_orders.loc[i]['Estimated_Num_offers']
    SecNum =  math.ceil(Estimated_Num_offers / np.e)
    AllOffers = nonidx_joinedDf[nonidx_joinedDf['REFERENCE_NUMBER'] == i].sort_values(by='CREATED_ON_HQ', ascending=True)
    a =0 
    if Estimated_Num_offers == 1 and len(AllOffers) > 0:
        record = AllOffers.iloc[0]['RATE_USD']
        rates.append(record)
        break
        
    elif (Estimated_Num_offers > 1) and (len(AllOffers) > 0):
        for n in range(SecNum-1):
            est_cost = AllOffers.iloc[n]['My_ESTIMATED_COST_AT_ORDER']
            actual_cost = AllOffers.iloc[n]['RATE_USD']
            if actual_cost < est_cost:
                record = actual_cost
                rates.append(record)
                a=1
                break
        if a == 0 :
            record = min(AllOffers.iloc[:SecNum]['RATE_USD'])
            for num in AllOffers['RATE_USD']:
                if num < record or (num == np.array(AllOffers['RATE_USD'])[-1]):
                    record = num
                    rates.append(record)
                    break


# In[26]:


our_avg_rate = np.mean(rates)
our_avg_rate


# In[27]:


Flock_avg_rate = np.mean(nonidx_joinedDf[nonidx_joinedDf['LOAD_DELIVERED_FROM_OFFER'] == True]['RATE_USD'])
Flock_avg_rate


# In[ ]:





# In[ ]:





# In[ ]:




