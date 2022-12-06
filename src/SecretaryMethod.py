import numpy as np
def runSextacy(refNums,testSetdf,offers):
    offers = offers[['REFERENCE_NUMBER','RATE_USD','CREATED_ON_HQ','CARRIER_ID']]
    testDF = testSetdf[['REFERENCE_NUMBER','EstimatedNumOffs','ESTIMATED_COST_AT_ORDER']]
    
    ReferenceNumber = []
    rates = []
    carrier = []

    for i in range(len(refNums)):
        order = testSetdf[testSetdf['REFERENCE_NUMBER'] == refNums[i]]
        offs = offers[offers['REFERENCE_NUMBER'] == refNums[i]].sort_values(by='CREATED_ON_HQ', ascending=True)
        estimatedNumsOffer = order['EstimatedNumOffs'][i]
        secNum = round(estimatedNumsOffer/np.e)
        acceptedInSec = 0
        if len(offs) > 0:
            if estimatedNumsOffer == 1:
                record = offs.iloc[0]['RATE_USD']
                ReferenceNumber.append(refNums[i])
                rates.append(record)
                carrier.append(offs.iloc[0]['CARRIER_ID'])
            else:
                estimatedCost = order['ESTIMATED_COST_AT_ORDER'][i]
                for n in range(secNum-1):
                    actual_cost = offs.iloc[n]['RATE_USD']
                    if actual_cost < estimatedCost:
                        rates.append(actual_cost)
                        ReferenceNumber.append(refNums[i])
                        carrier.append(offs.iloc[0]['CARRIER_ID'])
                        acceptedInSec = 1
                        break
                if acceptedInSec == 0:
                    record = min(offs.iloc[:secNum]['RATE_USD'])
                    offerRate = offs.iloc[secNum:]['RATE_USD']
                    for num in offerRate:
                        if num < record:
                            ReferenceNumber.append(refNums[i])
                            rates.append(num)
                            carrier.append(offs.iloc[0]['CARRIER_ID'])
                            break
    return {'ReferenceNumbers':ReferenceNumber,'Carrier':carrier,'Rate':rates}
    
