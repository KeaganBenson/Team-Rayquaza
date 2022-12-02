import pandas as pd

def clean_orders(orders):
    # converting time to dt and creating time difference
    
    orders['ORDER_DATETIME_PST'] = pd.to_datetime(orders['ORDER_DATETIME_PST'])
    orders['PICKUP_DEADLINE_PST'] = pd.to_datetime(orders['PICKUP_DEADLINE_PST'])
    orders['Time_between_Order_pickup'] = (orders['PICKUP_DEADLINE_PST'] - orders['ORDER_DATETIME_PST'])
    
    # filling nulls with mean square distance
    same = orders[orders['ORIGIN_3DIGIT_ZIP']==orders['DESTINATION_3DIGIT_ZIP']]
    mean_same_distance = same['APPROXIMATE_DRIVING_ROUTE_MILEAGE'].dropna().mean()
    orders['APPROXIMATE_DRIVING_ROUTE_MILEAGE'] = orders['APPROXIMATE_DRIVING_ROUTE_MILEAGE'].fillna(mean_same_distance)

    # fill FD enabled with false
    orders['FD_ENABLED'] = orders['FD_ENABLED'].fillna(False)
    orders = orders.dropna()
    return orders
    

def clean_offers(offers):
    offers['CREATED_ON_HQ'] = pd.to_datetime(offers['CREATED_ON_HQ'])
    return offers